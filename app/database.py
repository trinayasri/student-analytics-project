"""
database.py - Database Connection and Session Management

This module manages the SQLite connection using SQLAlchemy ORM.
It defines:
- Engine: The core interface to the SQLite database.
- SessionLocal: Factory for creating database sessions for each request.
- Base: Declarative base class from which all models inherit.
- get_db(): A dependency generator that yields a database session and ensures
  it is closed after the request completes.
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# SQLite database file path (persisted in project root)
# Can be overridden via DATABASE_URL environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./student_analytics.db")

# check_same_thread=False is needed only for SQLite because FastAPI handles
# requests across multiple threads, and SQLite by default restricts access to the creating thread.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False  # Set to True if SQL query debugging is desired
)

# SessionLocal is the session factory; autocommit=False ensures transactions are explicit
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session to route handlers.
    
    Using a Python generator with `yield` ensures the session is always
    closed cleanly in the `finally` block, preventing database connection leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
