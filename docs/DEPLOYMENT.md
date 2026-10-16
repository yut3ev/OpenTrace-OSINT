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
git clone https://github.com/yut3ev/OpenTrace-OSINT.git
cd OpenTrace-OSINT

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

| Variable | Alias | Default Value | Description |
|---|---|---|---|
| `OPENTRACE_STORAGE_MODE` | `OPENTRACE_STORAGE` | `sqlite` | Storage backend (`sqlite` for persistent, `memory` for volatile). |
| `OPENTRACE_SQLITE_PATH` | - | `opentrace.db` | File path for SQLite database when mode is `sqlite`. |
| `OPENTRACE_REQUIRE_AUTH` | - | `true` | Enforces authentication on investigation creation and exports. |
| `OPENTRACE_MAX_CONCURRENCY` | - | `5` | Global maximum concurrent HTTP/DNS tasks. |
| `OPENTRACE_PER_HOST_CONCURRENCY` | - | `2` | Per-domain concurrent connection limiter. |
| `OPENTRACE_DEFAULT_TIMEOUT` | `OPENTRACE_REQUEST_TIMEOUT_SECONDS` | `10.0` | Default HTTP timeout per module request in seconds. |
| `OPENTRACE_MAX_RUNTIME` | `OPENTRACE_MAX_RUNTIME_SECONDS` | `60.0` | Global timeout limit per investigation in seconds. |
| `OPENTRACE_CORS_ORIGINS` | - | `http://localhost:5173,...` | Comma-separated allowed frontend origins. |
| `OPENTRACE_CORS_ORIGIN_REGEX` | - | *(optional)* | Regular expression for dynamic CORS domains (e.g. `^https:\/\/.*\.vercel\.app$`). |
| `OPENTRACE_JWT_SECRET` | `JWT_SECRET` | *(dev default)* | High-entropy random secret for signing session JWT tokens. |
| `OPENTRACE_ACCESS_TOKEN_EXPIRE_MINUTES` | - | `10080` | JWT expiration duration in minutes (default 7 days). |
| `OPENTRACE_LOG_LEVEL` | - | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `OPENTRACE_USER_AGENT` | - | `OpenTrace/0.1 (...)` | Default User-Agent header for public requests. |
| `HIBP_API_KEY` | - | *(optional)* | Authorized API key for HaveIBeenPwned lookup adapter. |
| `NUMVERIFY_API_KEY` | - | *(optional)* | Authorized API key for Numverify phone provider adapter. |
| `TWILIO_ACCOUNT_SID` | - | *(optional)* | Twilio account SID for authorized carrier lookups. |
| `TWILIO_AUTH_TOKEN` | - | *(optional)* | Twilio authentication token for carrier lookups. |

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

### A. Backend Deployment on Render.com (FastAPI + Docker + PostgreSQL)

Render's Free Web Service plan runs containers with an **ephemeral disk** (local SQLite files are erased when the service restarts or spins down). In addition, Render **disallows persistent disk mounts (`disk:`) on Free plans**.

To achieve true zero-cost, persistent storage in production, OpenTrace includes native **PostgreSQL storage** (`PostgreSQLStorage`) alongside a free managed PostgreSQL database.

#### Step-by-Step Render Deployment:
1. Sign up for a free account on [Render](https://render.com).
2. Go to **Blueprints** and click **New Blueprint Instance**.
3. Connect your GitHub repository: `https://github.com/yut3ev/OpenTrace-OSINT.git`.
4. Render automatically parses `render.yaml` and sets up:
   - **`opentrace-api`**: Docker Web Service running the repository `Dockerfile`.
     - Automatically listens on dynamic Render `$PORT`.
     - Health check path configured at `/health` (HTTP 200).
     - Security enforced with `OPENTRACE_REQUIRE_AUTH=true`.
     - Cryptographically secure JWT secret generated automatically (`generateValue: true`).
   - **`opentrace-db`**: Free Managed PostgreSQL database instance.
     - `DATABASE_URL` is automatically wired into the API service via `fromDatabase`.
     - OpenTrace automatically runs migrations on startup, creating the schema and indexes.
5. Click **Apply**.
6. Once deployed, note your backend URL (e.g., `https://opentrace-api.onrender.com`).

> **External PostgreSQL Alternatives (Neon / Supabase):**
> If you prefer using a serverless PostgreSQL database (e.g. [Neon.tech](https://neon.tech) or [Supabase](https://supabase.com), both offering generous free tiers that never expire), simply set the `DATABASE_URL` environment variable on your Render service to your PostgreSQL connection string:
> `DATABASE_URL=postgresql://user:password@ep-sample-123.us-east-2.aws.neon.tech/opentrace?sslmode=require`

---

### B. Frontend Deployment on Vercel (React + TypeScript + Vite)

1. Sign up or log in to [Vercel](https://vercel.com).
2. Click **Add New > Project** and import `yut3ev/OpenTrace-OSINT`.
3. In project configuration:
   - **Framework Preset:** Vite
   - **Root Directory:** `./` (or `frontend`)
   - **Build Command:** `cd frontend && npm install && npm run build` (automatic via root `vercel.json`)
   - **Output Directory:** `frontend/dist`
4. In **Environment Variables**, add:
   - `VITE_API_BASE_URL`: Your Render backend URL (e.g. `https://opentrace-api.onrender.com`, **without** trailing slash).
5. Click **Deploy**.
6. Vercel builds the bundle and serves it globally with automatic HTTPS and SPA routing via `vercel.json`.

---

### C. Connect Frontend & Backend (CORS & Verification)

1. After Vercel deployment completes, copy your frontend domain (e.g., `https://opentrace-osint.vercel.app`).
2. In your Render Dashboard, navigate to **`opentrace-api` > Environment**:
   - Update `OPENTRACE_CORS_ORIGINS` to include your Vercel domain:
     `https://opentrace-osint.vercel.app,http://localhost:5173`
   - Render will automatically redeploy the backend with the updated CORS configuration.
3. Open your Vercel frontend URL in the browser:
   - Navigate to the **Sources (149)** tab to verify active source connectivity.
   - Click **Sign Up** to create your initial administrator account.
   - Launch your first OSINT investigation!

---

### D. Zero-Cost Free-Tier Architectural Guarantees
- **Total API cost:** $0 (149 active adapters operate on public endpoints without paid API subscriptions).
- **RAM Footprint:** ~85 MB resident memory during active search (well within 512 MB free-tier limits).
- **Persistent Storage:** Fully persistent investigations and user records stored in PostgreSQL.
- **Graceful Concurrency:** Semaphores cap concurrency to prevent memory spikes on container instances.

