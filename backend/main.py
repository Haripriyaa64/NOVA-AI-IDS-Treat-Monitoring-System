"""
NOVA — AI Voice Assistant Backend
main.py | FastAPI + Groq + JWT Auth + Chat History + FIXED CORS + Validation
"""

import os
import traceback
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from sqlalchemy.orm import Session
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
    raise RuntimeError("GROQ_API_KEY missing in .env")

client = Groq(api_key=GROQ_API_KEY)

app = FastAPI(title="NOVA AI Backend", version="3.0")

# Create DB tables on startup
init_db()

# ── ✅ FIXED CORS - SPECIFIC ORIGINS ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "https://nova-ai-voice-assistant-jade.vercel.app",  # Your Vercel URL
        "https://nova-ai-voice-assistant.onrender.com",     # Your Render URL
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None

# ── SYSTEM PROMPT ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are NOVA, a smart, friendly AI voice assistant.
Keep responses concise and natural — they will be read aloud.
No markdown, no bullet points, no asterisks. Just clear conversational sentences.
If you don't know something, say so honestly."""

# ══════════════════════════════════════════════════════════════════════════════
# ✅ FIXED AUTH ROUTES - WITH PASSWORD VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """
    Creates a new user account.
    ✅ VALIDATION: email, password length (6-72 chars), no duplicates
    """
    if not data.email or not data.password:
        raise HTTPException(status_code=400, detail="Email and password are required.")

    # ✅ CRITICAL: Validate password length for bcrypt compatibility
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    
    if len(data.password) > 72:
        raise HTTPException(status_code=400, detail="Password must be less than 72 characters.")

    # Validate email format
    if "@" not in data.email or "." not in data.email:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")

    existing = db.query(User).filter(User.email == data.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    try:
        user = User(
            email    = data.email.lower().strip(),
            password = hash_password(data.password)
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_token(user.id, user.email)
        return {"message": "Account created!", "token": token, "email": user.email}
    
    except Exception as e:
        db.rollback()
        print(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed. Please try again.")


@app.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """
    Verifies email + password.
    Returns a JWT token the frontend stores in localStorage.
    """
    if not data.email or not data.password:
        raise HTTPException(status_code=400, detail="Email and password are required.")

    user = db.query(User).filter(User.email == data.email.lower()).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = create_token(user.id, user.email)
    return {"token": token, "email": user.email}


# ══════════════════════════════════════════════════════════════════════════════
# SESSION ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/sessions/new")
def new_session(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a new empty chat session."""
    session = ChatSession(user_id=user_id, title="New Chat")
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"session_id": session.id, "title": session.title}


@app.get("/sessions")
def list_sessions(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns all chat sessions for the user, newest first."""
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return [{"id": s.id, "title": s.title, "created_at": str(s.created_at)} for s in sessions]


@app.get("/sessions/{session_id}/messages")
def get_session_messages(
    session_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns all messages in a session."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [{"role": m.role, "content": m.content, "created_at": str(m.created_at)} for m in messages]


@app.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes a chat session and all its messages."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    db.delete(session)
    db.commit()
    return {"message": "Chat deleted."}


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CHAT ROUTE
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/chat")
async def chat(
    data: ChatRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Main chat endpoint with full auth + history + session management.
    """
    user_input = data.message.strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Get or create session
    if data.session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == data.session_id,
            ChatSession.user_id == user_id
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found.")
    else:
        session = ChatSession(user_id=user_id, title="New Chat")
        db.add(session)
        db.commit()
        db.refresh(session)

    # Load previous messages from DB
    past_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    # Build Groq message list
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in past_messages:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": user_input})

    print(f"\n[Session {session.id}] User: {user_input[:60]}")

    # Call Groq
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=500,
            temperature=0.8,
        )
        reply = response.choices[0].message.content.strip()
        print(f"[Session {session.id}] NOVA: {reply[:60]}...")

    except Exception as e:
        print("GROQ ERROR:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")

    # Save messages to DB
    db.add(ChatMessage(session_id=session.id, role="user",      content=user_input))
    db.add(ChatMessage(session_id=session.id, role="assistant", content=reply))

    # Auto-title from first message
    if len(past_messages) == 0:
        session.title = user_input[:40] + ("…" if len(user_input) > 40 else "")

    db.commit()

    return {
        "reply":      reply,
        "session_id": session.id,
        "title":      session.title
    }


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/")
def home():
    return {"status": "NOVA v3.0 running ✅ — Auth + Sessions + Chat History"}
