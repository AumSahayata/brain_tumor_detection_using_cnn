import os
from fastapi import FastAPI, File, HTTPException, UploadFile
from io import BytesIO
from PIL import Image
from fastapi.responses import JSONResponse
import numpy as np
from pydantic import BaseModel
import tensorflow as tf  
import sqlite3
from backend.auth import generate_otp_uri, verify_otp

app = FastAPI()

# Load the pre-trained deep learning model
MODEL_PATH_2 = os.path.join(os.path.dirname(os.path.dirname(__file__)), "model", "50-10-4.h5")
MODEL_PATH_1 = os.path.join(os.path.dirname(os.path.dirname(__file__)), "model", "64-4.h5")
MODEL_PATH_3 = os.path.join(os.path.dirname(os.path.dirname(__file__)), "model", "128-64-4.h5")

model1 = tf.keras.models.load_model(MODEL_PATH_1)
model2 = tf.keras.models.load_model(MODEL_PATH_2)
model3 = tf.keras.models.load_model(MODEL_PATH_3)

# Define class labels
CLASS_NAMES = ["Glioma", "Meningioma", "No Tumor", "pituitary"]

# Image preprocessing function
def preprocess_image(image: Image.Image):
    image = image.resize((224, 224))
    image = np.array(image) / 255.0
    image = np.expand_dims(image, axis=0)
    return image

# API endpoint for image upload and prediction
@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    try:
        # Read the uploaded image
        image_bytes = await file.read()
        image = Image.open(BytesIO(image_bytes)).convert("L")
        # Preprocess image
        processed_image = preprocess_image(image)
        
        predictions = (
            model1.predict(processed_image),
            model2.predict(processed_image),
            model3.predict(processed_image)
        )
        
        print("Preds:", predictions)

        predictions = np.array(predictions)
        final_prediction = np.mean(predictions, axis=0)

        print("Final:", final_prediction)
        
        predicted_class = CLASS_NAMES[np.argmax(final_prediction)]  # Get highest probability class
        confidence = np.max(final_prediction)  # Get confidence score
        
        print(predicted_class)
        print(confidence)
        
        return {
            "filename": file.filename,
            "predicted_class": predicted_class,
            "confidence": float(confidence)
        }
    
    except Exception as e:
        return {"error": str(e)}

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "users.db")

def get_user_by_username(username):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_user_secret(username):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT otp_secret FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Request models
class OTPRequest(BaseModel):
    username: str

class OTPVerify(BaseModel):
    username: str
    otp: str

# Endpoint to verify OTP
@app.post("/verify-otp/")
def verify_otp_endpoint(data: OTPVerify):
    user = get_user_by_username(data.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if verify_otp(data.username, data.otp):
        return {"message": "OTP verified successfully"}
    else:
        raise HTTPException(status_code=400, detail="Invalid OTP")

# Endpoint to request OTP setup (returns QR code URI)
@app.post("/request-otp/")
def request_otp(data: OTPRequest):
    user = get_user_by_username(data.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    secret = get_user_secret(data.username)
    otp_uri = generate_otp_uri(data.username, secret)
    
    return JSONResponse(content={"otp_uri": otp_uri})


