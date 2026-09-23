#!/bin/bash
# OcuPulse Multi-Portal Launch Script (macOS / Linux)

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

echo "[1/3] Starting FastAPI Backend on http://localhost:8000 ..."
PYTHONPATH="backend:.:$PYTHONPATH" ./venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo "[2/3] Starting User Screening Frontend on http://localhost:5173 ..."
(cd frontend && npx vite --host 0.0.0.0 --port 5173) &
USER_FRONTEND_PID=$!

echo "[3/3] Starting Admin & Systems Console on http://localhost:5174 ..."
(cd admin_frontend && npx vite --host 0.0.0.0 --port 5174) &
ADMIN_FRONTEND_PID=$!

trap "kill $BACKEND_PID $USER_FRONTEND_PID $ADMIN_FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM EXIT

echo ""
echo ">> All OcuPulse portals are active!"
echo ">> 👤 Patient & User Screening: http://localhost:5173"
echo ">> 🛡️ Admin & Systems Console:    http://localhost:5174"
echo ">> ⚙️ Backend API Swagger Docs:   http://localhost:8000/docs"
echo ">> Press Ctrl+C to stop all services."
echo ""

wait
