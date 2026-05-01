"""
NOVA — AI Voice Assistant Backend
main.py  |  FastAPI + Groq
"""

import os
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from groq import Groq
from dotenv import load_dotenv

# ── Load .env file ──────────────────────────────────────────────────────────
load_dotenv()

app = FastAPI(title="NOVA AI Backend", version="2.1")

# ── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Groq client ─────────────────────────────────────────────────────────────
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

# ── System prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are NOVA, a friendly, witty, and intelligent AI voice assistant.
You answer clearly and concisely since your responses will be read aloud.
Avoid using markdown, bullet points, or special characters in your responses.
Keep answers conversational and natural-sounding.
If you don't know something, say so honestly."""

# ── Request schema ───────────────────────────────────────────────────────────
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = []


# ── Helper: map Groq errors to human-readable fixes ─────────────────────────
def get_fix_hint(e: Exception) -> str:
    msg = str(e).lower()
    if "401" in msg or "invalid api key" in msg or "authentication" in msg:
        return (
            "Your API key is INVALID or EXPIRED. "
            "Go to https://console.groq.com -> API Keys -> create a new one, "
            "then update your .env file."
        )
    if "429" in msg or "rate limit" in msg or "quota" in msg:
        return (
            "You hit the rate limit. Wait 1 minute and try again. "
            "Free tier rate limits may apply. Try again after some time."
        )
    if "model" in msg and ("not found" in msg or "does not exist" in msg):
        return (
            "Model name is wrong. "
            "Use one of: llama-3.1-8b-instant, llama-3.1-8b-instant, mixtral-8x7b-32768"
        )
    if "connection" in msg or "timeout" in msg:
        return "Network issue — check your internet connection."
    return f"Unknown error. Full message: {str(e)}"


# ── KEY TEST ROUTE ───────────────────────────────────────────────────────────
# Open http://127.0.0.1:8000/test-key in your browser to verify your setup
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


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/")
def home():
    return {"status": "NOVA backend is running", "version": "2.1"}


# ── Main chat route ──────────────────────────────────────────────────────────
@app.post("/chat")
async def chat(data: ChatRequest):
    user_input = data.message.strip()

    if not user_input:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Build messages: system + history + new message
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in data.history[:-1]:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": user_input})

    print(f"\nUser: {user_input}")
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
        # Print FULL error in your terminal — read this to understand what went wrong
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