"""
auth.py — Password hashing + JWT token creation/verification.

WHY THIS FILE EXISTS SEPARATELY:
  Keeps auth logic out of main.py so it stays clean.
  main.py imports these functions instead of duplicating them.

CRITICAL FIX from old code:
  Old auth.py had SECRET_KEY = "supersecretkey" hardcoded.
  main.py loaded SECRET_KEY from .env.
  Result: tokens created by auth.py couldn't be verified by main.py.
  Fix: BOTH files now read SECRET_KEY from .env via os.getenv().
"""

import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production-please")
ALGORITHM  = "HS256"
TOKEN_EXPIRE_HOURS = 24 * 7  # 7 days — users stay logged in

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Turns 'mypassword' → '$2b$12$...' (bcrypt hash). Never store raw passwords."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Returns True if the plain password matches the stored hash."""
    return pwd_context.verify(plain, hashed)


def create_token(user_id: int, email: str) -> str:
    """
    Creates a signed JWT token containing user_id + email.
    The token expires in TOKEN_EXPIRE_HOURS hours.
    Frontend stores this in localStorage and sends it with every request.
    """
    payload = {
        "user_id": user_id,
        "email":   email,
        "exp":     datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decodes and validates a JWT token.
    Raises JWTError if expired or tampered.
    Returns the payload dict {user_id, email, exp}.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])