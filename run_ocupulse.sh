#!/bin/bash
# OcuPulse Launch Script (macOS / Linux)

echo "======================================================="
echo "               OCUPULSE RETINAL ANALYSIS              "
echo "        AI-Assisted Retinal Vessel Screening          "
echo "======================================================="

# Check Python environment
if [ ! -d "venv" ]; then
    echo "[!] Virtual environment 'venv' not found. Creating..."
    python3 -m venv venv
    ./venv/bin/pip install -r backend/requirements.txt
fi

echo "[1/2] Starting FastAPI Backend on http://localhost:8000 ..."
PYTHONPATH="backend:.:$PYTHONPATH" ./venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo "[2/2] Starting Vite Frontend on http://localhost:5173 ..."
cd frontend && npm run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM EXIT

echo ""
echo ">> OcuPulse is ready!"
echo ">> Web Application: http://localhost:5173"
echo ">> Backend API Docs: http://localhost:8000/docs"
echo ">> Press Ctrl+C to stop both servers."
echo ""

wait
