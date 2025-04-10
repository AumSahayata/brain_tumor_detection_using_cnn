import random
import smtplib
from email.mime.text import MIMEText

otp_storage = {}

# Generate a 6-digit OTP
def generate_otp():
    return str(random.randint(100000, 999999))

# Send OTP via email
def send_otp(email):
    otp = generate_otp()
    otp_storage[email] = otp  # Store OTP (expires after validation)
    
    sender_email = "opt.chatbot@gmail.com"
    sender_password = "yqttzxhfcxzlrxfd"

    msg = MIMEText(f"Your verification code is: {otp}")
    msg["Subject"] = "Your 2FA Code"
    msg["From"] = sender_email
    msg["To"] = email

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Validate OTP
def verify_otp(email, user_otp):
    if email in otp_storage and otp_storage[email] == user_otp:
        del otp_storage[email]  
        return True
    return False