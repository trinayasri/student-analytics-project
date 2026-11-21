@echo off
title Student Performance Analytics Platform Launcher
echo ======================================================================
echo      AI-Powered Student Performance Analytics Platform
echo ======================================================================
echo.

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo [1/2] Launching FastAPI Backend (http://127.0.0.1:8000)...
start "FastAPI Backend - Student Analytics" cmd /k "cd /d \"%PROJECT_DIR%\" && .\venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

echo [INFO] Waiting for backend to initialize...
timeout /t 3 /nobreak >nul

echo [2/2] Launching Streamlit Dashboard (http://localhost:8501)...
start "Streamlit Dashboard - Student Analytics" cmd /k "cd /d \"%PROJECT_DIR%\" && .\venv\Scripts\activate.bat && streamlit run frontend/dashboard.py"

echo.
echo ======================================================================
echo Application successfully launched!
echo - FastAPI Swagger Docs: http://127.0.0.1:8000/docs
echo - Streamlit Dashboard:  http://localhost:8501
echo.
echo (Keep the two server terminal windows open while using the app)
echo ======================================================================
timeout /t 5
