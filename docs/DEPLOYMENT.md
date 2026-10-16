# OpenTrace OSINT — Deployment & Operations Guide

This guide details instructions for installing, configuring, running, and deploying OpenTrace OSINT in development and production environments.

---

## 1. System Requirements

- **Python:** 3.11, 3.12, or 3.13
- **Node.js:** 18 LTS, 20 LTS, or 22+ (for compiling the React frontend dashboard)
- **Memory:** Minimum 512 MB RAM (1 GB recommended for high concurrency)
- **Operating Systems:** Linux (Ubuntu/Debian, Fedora/RHEL), macOS, or Windows 10/11

---

## 2. Quickstart: Local Setup

### Step A: Clone and Install Python Backend

```bash
# Clone the repository
git clone https://github.com/your-org/opentrace.git
cd opentrace

# Create and activate virtual environment
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate
# On Windows PowerShell:
# .venv\Scripts\Activate.ps1

# Install in editable mode with development & testing dependencies
pip install -e ".[dev]"
```

### Step B: Build React Dashboard Frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

---

## 3. Running OpenTrace

### Option 1: Command-Line Interface (CLI)

OpenTrace provides a full-featured CLI powered by Typer and Rich:

```bash
# Verify installation
opentrace --version

# View catalog statistics and registered adapters
opentrace stats
opentrace sources --status implemented

# Run username search
opentrace investigate --username octocat

# Run multi-target search
opentrace investigate --username torvalds --email user@example.com --phone +14155552671

# Run name / people search
opentrace investigate --name "Alan Turing"

# Export findings to JSON, CSV, or HTML
opentrace export <INVESTIGATION_UUID> --format html --output report.html
```

### Option 2: FastAPI REST API Server

```bash
# Start API backend on port 8000
uvicorn opentrace.api.app:app --host 0.0.0.0 --port 8000 --reload
```

- **Interactive API Documentation (Swagger UI):** `http://localhost:8000/docs`
- **Alternative ReDoc UI:** `http://localhost:8000/redoc`
- **Health Check Endpoint:** `http://localhost:8000/health`
- **Source Catalog Endpoint:** `http://localhost:8000/api/v1/sources`

### Option 3: Web Dashboard (Development Server)

```bash
cd frontend
npm run dev
# Access UI at http://localhost:5173
```

---

## 4. Configuration & Environment Variables

OpenTrace is configured via standard environment variables or a `.env` file at the repository root:

| Variable | Default Value | Description |
|---|---|---|
| `OPENTRACE_STORAGE_MODE` | `memory` | Storage backend (`memory` or `sqlite`). |
| `OPENTRACE_SQLITE_PATH` | `opentrace.db` | File path for SQLite database when mode is `sqlite`. |
| `OPENTRACE_MAX_CONCURRENCY` | `10` | Global maximum concurrent HTTP/DNS tasks. |
| `OPENTRACE_PER_HOST_CONCURRENCY` | `2` | Per-domain concurrent connection limiter. |
| `OPENTRACE_MAX_RUNTIME` | `45` | Global timeout limit per investigation in seconds. |
| `OPENTRACE_LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `OPENTRACE_USER_AGENT` | `OpenTrace-OSINT/0.1.0` | Default User-Agent header for public requests. |
| `HIBP_API_KEY` | *(optional)* | Authorized API key for HaveIBeenPwned lookup adapter. |
| `NUMVERIFY_API_KEY` | *(optional)* | Authorized API key for Numverify phone provider adapter. |

---

## 5. Docker Deployment

### Building and Running via Dockerfile

```bash
# Build multi-stage container
docker build -t opentrace:latest .

# Run container with SQLite persistence volume
docker run -d \
  --name opentrace \
  -p 8000:8000 \
  -e OPENTRACE_STORAGE_MODE=sqlite \
  -e OPENTRACE_SQLITE_PATH=/data/opentrace.db \
  -v opentrace_data:/data \
  opentrace:latest
```

---

## 6. Reverse Proxy Configuration (Nginx)

When deploying behind Nginx or Caddy, disable proxy buffering for the Server-Sent Events (SSE) endpoint:

```nginx
server {
    listen 80;
    server_name opentrace.example.com;

    # Serve static frontend build
    location / {
        root /var/www/opentrace/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Real-time SSE event stream (buffering must be off)
    location ~* /api/v1/investigations/.+/events$ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }
}
```

---

## 7. Verification & Health Checks

Run the verification suite to ensure all components are healthy:

```bash
# Run pytest automated test suite
pytest -v

# Run code style & static analysis
ruff check .
ruff format --check .
mypy src/opentrace

# Run frontend type check and build
cd frontend && npm run lint && npm run build
```

---

## 8. Free-Tier Cloud Deployment Guide ($0 / Month)

OpenTrace is architected specifically for zero-cost operation on public free tiers:

### A. Frontend Deployment on Vercel
1. Import repository on [Vercel](https://vercel.com).
2. Root directory is automatically handled by the top-level `vercel.json` (or set Root Directory to `frontend`).
3. Set Environment Variable:
   - `VITE_API_BASE_URL`: `https://opentrace-api.onrender.com` (your backend URL)
4. Deploy: Vercel compiles React TypeScript static assets and caches them across its global edge network.

### B. Backend Deployment on Render.com
1. Create a free account on [Render](https://render.com).
2. Connect your GitHub repository and click **New > Blueprint**.
3. Select `render.yaml` in the repository root.
4. Render provisions:
   - `opentrace-api`: Python 3.12 Web Service on Free plan (512 MB RAM).
   - `opentrace-data`: 1 GB persistent SQLite volume attached to `/data/opentrace.db`.
5. Automatic cold-start handling: SQLite automatically runs migrations on startup (`src/opentrace/storage/migrations/runner.py`) in under 50ms.

### C. Railway / Fly.io Alternative
- **Railway:** Deploy directly using the provided `Dockerfile` and `docker-compose.yml`.
- **Fly.io:** Run `fly launch` using `fly.toml` with `min_machines_running = 0` to sleep when idle and wake on request.

### D. Zero-Cost Free-Tier Architectural Guarantees
- **Total API cost:** \$0 (149 active adapters run without requiring paid API keys).
- **RAM Footprint:** ~85 MB resident memory during active search (well within 512 MB free-tier limits).
- **Graceful Concurrency:** Semaphores cap concurrency to prevent memory spikes.

