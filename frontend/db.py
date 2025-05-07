import sqlite3
import hashlib

import pyotp

# Function to create the users table
def create_users_table():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            otp_secret TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to register a new user
def register_user(username, email, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    otp_secret = pyotp.random_base32()  # Generate TOTP secret here
    try:
        c.execute("INSERT INTO users (username, email, password_hash, otp_secret) VALUES (?, ?, ?, ?)", 
                (username, email, hash_password(password), otp_secret))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Function to validate user login
def login_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    if user and user[0] == hash_password(password):
        return True
    return False
