import pyotp
import sqlite3
import os

# Get the path to the SQLite database
def get_db_path():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "users.db")

# Generate a new TOTP secret and store it
def generate_and_store_secret(username):
    secret = pyotp.random_base32()
    db_path = get_db_path
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET otp_secret=? WHERE username=?", (secret, username))
    conn.commit()
    conn.close()
    return secret

# Retrieve stored secret
def get_user_secret(username):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT otp_secret FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Generate otpauth:// URI for QR code (for Google Authenticator)
def generate_otp_uri(username, secret):
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name="IBM Project")

# Verify TOTP code
def verify_otp(username, user_otp):
    secret = get_user_secret(username)
    if not secret:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(user_otp)
