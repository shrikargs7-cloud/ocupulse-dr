@echo off
REM OcuPulse Launch Script for Windows

echo =======================================================
echo                OCUPULSE RETINAL ANALYSIS              
echo         AI-Assisted Retinal Vessel Screening          
echo =======================================================

echo [1/2] Starting FastAPI Backend on http://localhost:8000 ...
start "OcuPulse Backend" cmd /k ".\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Starting Vite Frontend on http://localhost:5173 ...
cd frontend
start "OcuPulse Frontend" cmd /k "npm run dev"

echo.
echo >> OcuPulse launched!
echo >> Open browser at: http://localhost:5173
echo >> Backend API Docs: http://localhost:8000/docs
echo.
