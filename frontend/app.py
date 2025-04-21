import streamlit as st
import requests
import io
from PIL import Image
from db import create_users_table, register_user, login_user  # Import DB functions

# FastAPI backend URL
FASTAPI_URL = "http://127.0.0.1:8000/predict/"  # Update with actual URL if deployed
OTP_REQUEST_URL = "http://127.0.0.1:8000/request-otp/"  # FastAPI endpoint to request OTP
OTP_VERIFY_URL = "http://127.0.0.1:8000/verify-otp/"  # FastAPI endpoint to verify OTP

# Create users table on startup
create_users_table()

# Streamlit UI
def main():
    st.title("Brain Tumor Classification")
    
    # Initialize session states if they don't exist
    if "signup" not in st.session_state:
        st.session_state.signup = False
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "otp_sent" not in st.session_state:
        st.session_state.otp_sent = False
    if "username" not in st.session_state:
        st.session_state.username = None

    if st.session_state.authenticated:
        tumor_prediction_ui()
    elif st.session_state.signup:
        signup_page()
    else:
        login_page()

def signup_page():
    st.subheader("Create an Account")
    new_username = st.text_input("Username")
    new_email = st.text_input("Email")
    new_password = st.text_input("Password", type="password")
    if st.button("Sign Up"):
        if register_user(new_username, new_email, new_password):
            st.success("Account created successfully! Please log in.")
            st.session_state.signup = False
        else:
            st.error("Username or Email already exists. Try a different one.")
    if st.button("Back to Login"):
        st.session_state.signup = False

def login_page():
    st.subheader("Login to Your Account")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login_user(username, password):
            response = requests.post(OTP_REQUEST_URL, json={"username": username})
            if response.status_code == 200:
                st.session_state.otp_sent = True
                st.session_state.username = username
                st.success("OTP sent! Check your email.")
            else:
                st.error("Error sending OTP.")
        else:
            st.error("Invalid credentials. Try again.")
    
    if st.button("Create an Account"):
        st.session_state.signup = True
        st.rerun()

    if st.session_state.otp_sent and st.session_state.username:
        otp = st.text_input("Enter the OTP sent to your email", type="password")
        if st.button("Verify OTP"):
            response = requests.post(OTP_VERIFY_URL, json={"username": st.session_state.username, "otp": otp})
            if response.status_code == 200:
                st.session_state.authenticated = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid OTP. Try again.")

def tumor_prediction_ui():
    st.subheader("Upload an MRI scan to classify it into one of the tumor types.")
    uploaded_file = st.file_uploader("Choose an MRI image", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file).convert("L")
        st.image(image, caption="Uploaded Image", width=500)
        
        # Convert image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        if st.button("Predict"):  # Predict button
            with st.spinner("Predicting..."):
                try:
                    response = requests.post(FASTAPI_URL, files={"file": img_byte_arr})
                    if response.status_code == 200:
                        result = response.json()
                        if result['confidence'] > 0.6:
                            st.success(f"Predicted Class: {result['predicted_class']}")
                            st.write(f"Confidence: {result['confidence'] * 100 :.2f}%")
                        else:
                            st.warning(f"The model is not sure. Please consoult a doctor.")
                    else:
                        st.error("Failed to get a response from the backend.")
                except Exception as e:
                    st.error(f"Error: {e}")
    if st.button("Logout"):
        # Clear all session states
        st.session_state.authenticated = False
        st.session_state.signup = False
        st.session_state.otp_sent = False
        st.session_state.username = None
        st.rerun()

if __name__ == "__main__":
    main()
