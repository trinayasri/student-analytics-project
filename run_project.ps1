# AI-Powered Student Performance Analytics Platform PowerShell Launcher
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "       AI-Powered Student Performance Analytics Platform" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectDir'; Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

Start-Sleep -Seconds 3

Write-Host "[2/2] Starting Streamlit Dashboard on http://localhost:8501 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectDir'; Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\venv\Scripts\Activate.ps1; streamlit run frontend/dashboard.py"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "Application launched successfully!" -ForegroundColor Green
Write-Host "- Swagger Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "- Dashboard:    http://localhost:8501" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Green
