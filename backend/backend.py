from fastapi import FastAPI, File, HTTPException, UploadFile
from io import BytesIO
from PIL import Image
import numpy as np
from pydantic import BaseModel
import tensorflow as tf  
import sqlite3
import os
from auth import send_otp, verify_otp

app = FastAPI()

# Load the pre-trained deep learning model
MODEL_PATH = "model/64-4.h5"  
model = tf.keras.models.load_model(MODEL_PATH)

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

        # Perform prediction
        predictions = model.predict(processed_image)
        predicted_class = CLASS_NAMES[np.argmax(predictions)]  # Get highest probability class
        confidence = float(np.max(predictions))  # Get confidence score

        return {
            "filename": file.filename,
            "predicted_class": predicted_class,
            "confidence": confidence
        }
    
    except Exception as e:
        return {"error": str(e)}

def get_email_by_username(username):
    conn = sqlite3.connect('frontend/users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Request models
class OTPRequest(BaseModel):
    username: str

class OTPVerify(BaseModel):
    username: str
    otp: str

# Endpoint to request OTP
@app.post("/request-otp/")
def request_otp(data: OTPRequest):
    email = get_email_by_username(data.username)
    if not email:
        raise HTTPException(status_code=404, detail="User not found")

    if send_otp(email):
        return {"message": "OTP sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Error sending OTP")

# Endpoint to verify OTP
@app.post("/verify-otp/")
def verify_otp_endpoint(data: OTPVerify):
    email = get_email_by_username(data.username)
    if not email:
        raise HTTPException(status_code=404, detail="User not found")

    if verify_otp(email, data.otp):
        return {"message": "OTP verified successfully"}
    else:
        raise HTTPException(status_code=400, detail="Invalid OTP")
