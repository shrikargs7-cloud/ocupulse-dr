@echo off
REM OcuPulse Multi-Portal Launch Script for Windows

echo =======================================================
echo                OCUPULSE RETINAL ANALYSIS              
echo         AI-Assisted Retinal Vessel Screening          
echo =======================================================

echo [1/3] Starting FastAPI Backend on http://localhost:8000 ...
start "OcuPulse Backend" cmd /k ".\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/3] Starting User Screening Frontend on http://localhost:5173 ...
start "OcuPulse User App" cmd /k "cd frontend && npx vite --port 5173"

echo [3/3] Starting Admin & Systems Console on http://localhost:5174 ...
start "OcuPulse Admin Console" cmd /k "cd admin_frontend && npx vite --port 5174"

echo.
echo >> All OcuPulse portals launched!
echo >> User Screening App: http://localhost:5173
echo >> Admin Systems Console: http://localhost:5174
echo >> Backend API Docs: http://localhost:8000/docs
echo.
