import streamlit as st
import requests
import io
import qrcode
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
            st.success("Account created successfully!")

            # Request QR code URI for Google Authenticator setup
            response = requests.post(OTP_REQUEST_URL, json={"username": new_username})
            if response.status_code == 200:
                otp_uri = response.json().get("otp_uri")
                if otp_uri:
                    st.info("Scan this QR code with Google Authenticator to complete setup.")
                    img = qrcode.make(otp_uri)
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    st.image(buf.getvalue(), caption="Scan this QR with Google Authenticator")
                else:
                    st.warning("OTP URI not returned.")
            else:
                st.error("Failed to generate OTP for the new account.")

            st.session_state.signup = False
        else:
            st.error("Username or Email already exists. Try a different one.")

    if st.button("Back to Login"):
        st.session_state.signup = False

def login_page():
    st.subheader("Login to Your Account")

    if "otp_sent" not in st.session_state:
        st.session_state.otp_sent = False
    if "username" not in st.session_state:
        st.session_state.username = ""

    # OTP not sent yet: show login form
    if not st.session_state.otp_sent:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if login_user(username, password):
                st.session_state.otp_sent = True
                st.session_state.username = username
                st.success("Open your Authenticator app and enter the code.")
            else:
                st.error("Invalid username or password.")

        if st.button("Create an Account"):
            st.session_state.signup = True
            st.rerun()

    # OTP has been sent: show OTP verification form
    if st.session_state.otp_sent and st.session_state.username:
        otp = st.text_input("Enter the OTP from your Authenticator app", type="password")
        if st.button("Verify OTP"):
            response = requests.post(OTP_VERIFY_URL, json={"username": st.session_state.username, "otp": otp})
            if response.status_code == 200:
                st.session_state.authenticated = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid OTP. Please try again.")


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
                        predicted_class = result['predicted_class']
                        confidence = result['confidence']

                        # Display Prediction Result
                        st.success(f"Predicted Class: {predicted_class}")
                        st.write(f"Confidence: {confidence * 100:.2f}%")

                        # More explanation
                        if confidence > 0.62:
                            st.write(f"The model predicts that there is a {predicted_class} with a high confidence of {confidence * 100:.2f}%.")
                            st.write("While the model shows confidence, it's important to follow up with a healthcare professional for confirmation and to discuss the next steps.")
                        else:
                            st.warning("The model is not very confident in this prediction. Please consult a doctor for a professional diagnosis and further tests.")
                        
                        # Extra suggestions
                        st.write("Next steps could include:")
                        st.write("- Consult a medical professional for a more detailed diagnosis.")
                        st.write("- Discuss further diagnostic imaging or tests with your doctor.")
                        st.write("- Be aware of the symptoms of brain tumors and seek medical attention if needed.")
                    else:
                        st.error("Failed to get a response from the backend. Please try again later.")
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
