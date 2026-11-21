"""
config.py - Application Configuration & Environment Settings

Loads configuration from environment variables or .env file with safe defaults.
Centralizes secret keys, algorithm choices, and API connection details.
"""

import os
from typing import Optional

# Base API Configuration
API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
API_PORT: int = int(os.getenv("API_PORT", "8000"))
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./student_analytics.db")

# Security & JWT Configuration
SECRET_KEY: str = os.getenv("SECRET_KEY", "student-analytics-super-secret-jwt-key-2026-production-ready")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24)))  # 24 hours

# Gemini AI API Configuration
GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Default Academic Year
DEFAULT_ACADEMIC_YEAR: str = "2024-2025"
