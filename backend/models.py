"""
models.py — Database table definitions
Every column name here is the SINGLE source of truth.
main.py, auth.py must all match these names exactly.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    email      = Column(String, unique=True, index=True, nullable=False)
    password   = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # One user → many chat sessions
    sessions   = relationship("ChatSession", back_populates="user", cascade="all, delete")


class ChatSession(Base):
    """
    Represents one conversation thread (like a ChatGPT sidebar item).
    Each session has many ChatMessage rows.
    """
    __tablename__ = "chat_sessions"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    title      = Column(String, default="New Chat")      # auto-set from first message
    created_at = Column(DateTime, default=datetime.utcnow)

    user       = relationship("User", back_populates="sessions")
    messages   = relationship("ChatMessage", back_populates="session", cascade="all, delete")


class ChatMessage(Base):
    """
    One user↔bot exchange inside a session.
    """
    __tablename__ = "chat_messages"

    id         = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role       = Column(String, nullable=False)   # "user" or "assistant"
    content    = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session    = relationship("ChatSession", back_populates="messages")
    
class LoginLog(Base):

    __tablename__ = "login_logs"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, nullable=False)

    source_ip = Column(String, nullable=False)

    destination_ip = Column(String, nullable=False)

    user_agent = Column(Text)

    login_status = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    
class Alert(Base):
    """
    Stores IDS alerts generated from suspicious login activity.
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=True)
    source_ip = Column(String, nullable=False)
    attack_type = Column(String, nullable=False)
    risk_level = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
