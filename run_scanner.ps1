# EZYerrScanner One-Click Launcher
# This script starts the Unified Backend and the Vite Frontend simultaneously.

$ErrorActionPreference = "Stop"

# 1. Start Unified Backend (Port 8000)
Write-Host "Starting Unified Backend (SmartAgent + File Scanner)..." -ForegroundColor Cyan
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit -Command `".\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload`"" -WorkingDirectory "$PSScriptRoot\smartagent\backend"

# 2. Wait for Backend
Start-Sleep -Seconds 3

# 3. Start Frontend (Port 5173)
Write-Host "Starting Vite Frontend..." -ForegroundColor Green
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit -Command `"npx vite --host 0.0.0.0 --port 5173`"" -WorkingDirectory "$PSScriptRoot\frontend"

Write-Host "`nAll services starting!`" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:5173"
Write-Host "Backend API: http://localhost:8000/api"
Write-Host "Swagger Docs: http://localhost:8000/docs"
