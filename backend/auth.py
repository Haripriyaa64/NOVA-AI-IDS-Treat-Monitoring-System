"""
auth.py — Password hashing + JWT token creation/verification.
SWITCHED TO ARGON2 (more reliable than bcrypt for deployment)
"""

import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production-please")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24 * 7  # 7 days

# ✅ SWITCHED TO ARGON2 - more stable than bcrypt
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash password using Argon2 (more reliable than bcrypt).
    Never store raw passwords.
    """
    # Validate password length BEFORE hashing
    password = password[:100]  # Argon2 can handle longer passwords
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Returns True if plain password matches hashed version."""
    plain = plain[:100]  # Limit length
    return pwd_context.verify(plain, hashed)


def create_token(user_id: int, email: str) -> str:
    """
    Creates a signed JWT token containing user_id + email.
    Token expires in TOKEN_EXPIRE_HOURS hours.
    """
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decodes and validates a JWT token.
    Raises JWTError if expired or invalid.
    Returns payload {user_id, email, exp}.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
