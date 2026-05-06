"""
NOVA — AI Voice Assistant Backend
main.py | FastAPI + Groq + JWT Auth
"""

import os
import traceback
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from groq import Groq
from jose import JWTError
from dotenv import load_dotenv

from database import SessionLocal, init_db
from models import User, ChatSession, ChatMessage
from auth import hash_password, verify_password, create_token, decode_token

# ── Startup ──────────────────────────────────────────────────────────────────
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("=" * 60)
    print("ERROR: GROQ_API_KEY not found in environment!")
    print("  Fix: Create a .env file with this line:")
    print("  GROQ_API_KEY=your_actual_key_here")
    print("=" * 60)
    raise RuntimeError("GROQ_API_KEY missing. See above.")

print(f"Groq API Key loaded: {GROQ_API_KEY[:8]}...{GROQ_API_KEY[-4:]}")

client = Groq(api_key=GROQ_API_KEY)

app = FastAPI(title="NOVA AI Backend", version="2.1")

# Create DB tables on startup
init_db()

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DB Session Dependency ─────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── Auth Dependency ───────────────────────────────────────────────────────────
def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not logged in. Please login first.")
    try:
        token = authorization.replace("Bearer ", "").strip()
        payload = decode_token(token)
        return payload["user_id"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Session expired. Please login again.")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token.")

# ── Pydantic Schemas ──────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = []

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are NOVA, a friendly, witty, and intelligent AI voice assistant.
You answer clearly and concisely since your responses will be read aloud.
Avoid using markdown, bullet points, or special characters in your responses.
Keep answers conversational and natural-sounding.
If you don't know something, say so honestly."""

# ── Helper: map Groq errors to human-readable fixes ───────────────────────────
def get_fix_hint(e: Exception) -> str:
    msg = str(e).lower()
    if "401" in msg or "invalid api key" in msg or "authentication" in msg:
        return (
            "Your API key is INVALID or EXPIRED. "
            "Go to https://console.groq.com -> API Keys -> create a new one, "
            "then update your .env file."
        )
    if "429" in msg or "rate limit" in msg or "quota" in msg:
        return "You hit the rate limit. Wait 1 minute and try again."
    if "model" in msg and ("not found" in msg or "does not exist" in msg):
        return "Model name is wrong. Use: llama-3.1-8b-instant or llama-3.3-70b-versatile"
    if "connection" in msg or "timeout" in msg:
        return "Network issue — check your internet connection."
    return f"Unknown error. Full message: {str(e)}"


# ══════════════════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/register")
def register(data: RegisterRequest, db = Depends(get_db)):
    if not data.email or not data.password:
        raise HTTPException(status_code=400, detail="Email and password are required.")

    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    existing = db.query(User).filter(User.email == data.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user = User(
        email    = data.email.lower().strip(),
        password = hash_password(data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(user.id, user.email)
    return {"message": "Account created!", "token": token, "email": user.email}


@app.post("/login")
def login(data: LoginRequest, db = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower().strip()).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = create_token(user.id, user.email)
    return {"token": token, "email": user.email}


# ══════════════════════════════════════════════════════════════════════════════
# KEY TEST ROUTE
# open http://127.0.0.1:8000/test-key in browser to verify your setup
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/test-key")
async def test_key():
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Say: API key works!"}],
            max_tokens=20,
        )
        return {
            "status": "SUCCESS",
            "key_prefix": GROQ_API_KEY[:8] + "...",
            "model_reply": response.choices[0].message.content,
        }
    except Exception as e:
        return {
            "status": "FAILED",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "fix": get_fix_hint(e),
        }


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CHAT ROUTE
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/chat")
async def chat(
    data: ChatRequest,
    user_id: int = Depends(get_current_user)
):
    user_input = data.message.strip()

    if not user_input:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Build messages: system + history + new message
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in data.history[:-1]:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": user_input})

    print(f"\nUser [{user_id}]: {user_input}")
    print(f"History turns included: {len(data.history)}")

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=80,
            temperature=0.3,
        )

        reply = response.choices[0].message.content.strip()
        print(f"NOVA replied: {reply[:80]}...")
        return {"reply": reply}

    except Exception as e:
        print("\n" + "=" * 60)
        print("GROQ API ERROR:")
        print(f"  Type    : {type(e).__name__}")
        print(f"  Message : {str(e)}")
        traceback.print_exc()
        print("=" * 60)

        hint = get_fix_hint(e)
        raise HTTPException(
            status_code=500,
            detail=f"{type(e).__name__}: {str(e)} | Fix: {hint}"
        )


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/")
def home():
    return {"status": "NOVA backend is running", "version": "2.1"}