# OcuPulse Deployment Guide

This guide covers deployment options for OcuPulse across local workstations, on-premise clinic servers, and cloud environments.

---

## 1. System Requirements

### Hardware
- **Processor**: Intel/AMD x86_64 or Apple Silicon (M1/M2/M3/M4)
- **RAM**: Minimum 8 GB (16 GB recommended for high-throughput batch grading)
- **Disk**: 5 GB free disk space (excluding raw datasets)
- **Optional GPU**: NVIDIA GPU with CUDA 11.8+ for deep-learning batch acceleration

### Software Prerequisites
- Python 3.10 to 3.14
- Node.js 18+ and npm
- (Optional) MATLAB R2022b or later with Image Processing Toolbox, Deep Learning Toolbox, and Simulink

---

## 2. Quick Start (Local Development)

Execute the universal launcher script:
```bash
cd /Users/shrikar/Desktop/db/ocupluse
./run_ocupulse.sh
```

This starts:
1. **FastAPI Backend**: `http://localhost:8000`
2. **Vite Frontend**: `http://localhost:5173`

---

## 3. Database Configuration

OcuPulse uses a dual-engine database architecture:
- **Local Fallback**: SQLite (`backend/ocupluse.db`) with zero configuration.
- **Production Cloud**: Supabase PostgreSQL with connection pooling.

To enable Supabase:
1. Copy template:
   ```bash
   cp .env.example .env
   ```
2. Set your Supabase connection URI:
   ```env
   DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```
3. Initialize cloud tables:
   ```bash
   ./venv/bin/python scripts/test_supabase_connection.py
   ```
4. (Optional) Upload existing SQLite records:
   ```bash
   ./venv/bin/python scripts/migrate_sqlite_to_supabase.py
   ```

---

## 4. Production Containerization (Docker)

To deploy as a unified Docker container:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t ocupulse:latest .
docker run -p 8000:8000 --env-file .env ocupulse:latest
```
