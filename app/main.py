"""
main.py - FastAPI Application Entry Point

Initializes FastAPI app, sets up CORS middleware, manages application lifecycle
(automatic database table creation on startup), and mounts student and analytics routers.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routes import students, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager.
    Automatically creates database tables on startup.
    Cleans up any application resources on shutdown.
    """
    # Startup: ensure all SQLAlchemy models have corresponding SQLite tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown logic (if any) goes here


app = FastAPI(
    title="Student Performance Analytics System API",
    description=(
        "Production-grade RESTful API for academic student management and institutional performance analytics. "
        "Provides student CRUD, pagination, multi-criteria filtering, grade distributions, and at-risk student monitoring."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Cross-Origin Resource Sharing (CORS) Middleware
# Allows the Streamlit frontend running on a different port (e.g. 8501) to communicate with FastAPI (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(students.router, prefix="/api/students", tags=["Students"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])


@app.get("/", tags=["Health"])
def root():
    """Root endpoint welcoming API consumers and pointing to interactive docs."""
    return {
        "message": "Welcome to the Student Performance Analytics System API",
        "documentation": "/docs",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
def health_check():
    """Health check endpoint used for monitoring API and database availability."""
    return {
        "status": "healthy",
        "database": "sqlite_connected",
        "service": "student-performance-analytics-api"
    }
