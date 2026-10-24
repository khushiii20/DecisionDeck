"""
Database Connection & Session Configuration
Supports local SQLite development and cloud PostgreSQL (e.g. Supabase).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Default to local SQLite database if DATABASE_URL environment variable is not set
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./decisiondeck.db")

# For SQLite, check_same_thread=False is needed for multi-threaded FastAPI requests
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a database session per request
    and guarantees it is closed when the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
