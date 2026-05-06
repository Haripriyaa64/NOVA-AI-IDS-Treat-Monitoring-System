"""
database.py — SQLAlchemy engine, session, and Base.

HOW IT WORKS:
  - create_engine()   → connects Python to the SQLite file nova.db
  - SessionLocal()    → gives you a DB "cursor" to run queries
  - Base              → all models inherit from this so SQLAlchemy knows the table schema
  - create_all()      → reads all models and creates the tables if they don't exist yet
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite file will be created in the backend/ folder automatically
DATABASE_URL = "sqlite:///./nova.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # needed for SQLite + FastAPI threads
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def init_db():
    """
    Call this once at startup to create all tables.
    Safe to call multiple times — only creates tables that don't exist yet.
    """
    import models  # noqa: F401 — must import so Base knows about all models
    Base.metadata.create_all(bind=engine)
