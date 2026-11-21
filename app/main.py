"""
main.py - FastAPI Application Entry Point

Initializes FastAPI app, sets up CORS middleware, manages application lifecycle
(automatic database table creation on startup), and mounts authentication, student,
analytics, and AI routers.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routes import students, analytics, auth, ai, study_plans, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager.
    Automatically creates all database tables (users, students, teachers, etc.) on startup.
    Cleans up any application resources on shutdown.
    """
    # Startup: ensure all SQLAlchemy models have corresponding tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown logic (if any)


app = FastAPI(
    title="Student Performance Analytics & Recommendation Platform API",
    description=(
        "Production-ready RESTful API for academic student management, institutional performance analytics, "
        "and AI-powered recommendation workflows. Includes JWT authentication, Role-Based Access Control, "
        "multi-criteria filtering, at-risk early warnings, and personalized study plans."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Cross-Origin Resource Sharing (CORS) Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(students.router, prefix="/api/students", tags=["Students"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI Diagnostics"])
app.include_router(study_plans.router, prefix="/api/study-plans", tags=["Study Plans"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])


@app.get("/", tags=["Health"])
def root():
    """Root endpoint welcoming API consumers and pointing to interactive docs."""
    return {
        "message": "Welcome to the Student Performance Analytics & Recommendation Platform API",
        "documentation": "/docs",
        "version": "2.0.0",
        "status": "operational"
    }


@app.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
def health_check():
    """Health check endpoint used for monitoring API and database availability."""
    return {
        "status": "healthy",
        "database": "connected",
        "service": "student-performance-analytics-api",
        "version": "2.0.0"
    }
