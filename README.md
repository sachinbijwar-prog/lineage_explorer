# Enterprise Dependency & Lineage Explorer

A proof-of-concept lineage explorer for visualizing enterprise data dependencies.

The app has three main parts:

- **Frontend:** React + TypeScript + Vite + Cytoscape.js
- **Backend:** FastAPI
- **Graph store:** Neo4j

## Prerequisites

Install these before running the project:

- Docker Desktop
- Python 3.12 or newer
- Node.js 18 or newer
- npm

Make sure Docker Desktop is fully started before running Docker commands. If Docker is not running, you may see an error like:

```text
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
```

## Start Neo4j

From the project root:

```powershell
cd C:\git\lineage_explorer
docker compose -f docker\docker-compose.yml up -d neo4j
```

Neo4j browser will be available at:

```text
http://localhost:7474
```

Default credentials from `docker/docker-compose.yml`:

```text
username: neo4j
password: password
```

## Backend Setup

Create and activate a virtual environment if needed:

```powershell
cd C:\git\lineage_explorer
python -m venv backend\.venv
.\backend\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\backend\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
pip install -r backend\requirements.txt
```

Create `backend\.env` if it does not exist:

```text
APP_NAME=Enterprise Dependency & Lineage Explorer
APP_VERSION=0.1.0

NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=lineage
POSTGRES_USER=lineage
POSTGRES_PASSWORD=lineage
```

Start the backend:

```powershell
python -m uvicorn backend.app.main:app --reload
```

Backend API:

```text
http://127.0.0.1:8000
```

Swagger docs:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

## Frontend Setup

Open a second PowerShell terminal:

```powershell
cd C:\git\lineage_explorer\frontend
npm install
npm run dev
```

Frontend app:

```text
http://localhost:5173
```

## Demo Flow

1. Start Docker Desktop.
2. Start Neo4j.
3. Start the FastAPI backend.
4. Start the Vite frontend.
5. Open `http://localhost:5173`.
6. Click **Seed Demo Graph** if the graph is empty.
7. Try path highlighting with:

```text
source: ftp_handshake_01
target: vendor_hive_tbl
```

Expected path:

```text
ftp_handshake_01 -> trigger_ingest_sh -> raw_vendor_data -> beeline_load_job -> vendor_hive_tbl
```

## Useful API Endpoints

```text
GET  /health
GET  /api/v1/lineage/test
POST /api/v1/lineage/seed
GET  /api/v1/lineage/{node_id}
GET  /api/v1/lineage/upstream/{node_id}
GET  /api/v1/lineage/downstream/{node_id}
GET  /api/v1/lineage/impact/{node_id}
GET  /api/v1/lineage/search?q={query}
GET  /api/v1/path/{source_id}/{target_id}
```

## Troubleshooting

### Docker cannot connect

Start Docker Desktop and wait until it says Docker is running. Then retry:

```powershell
docker compose -f docker\docker-compose.yml up -d neo4j
```

### Backend starts but graph endpoints fail

This usually means Neo4j is not running or is not reachable on port `7687`.

Check containers:

```powershell
docker ps
```

Restart Neo4j:

```powershell
docker compose -f docker\docker-compose.yml restart neo4j
```

Then restart the backend.

### Frontend cannot reach backend

Make sure the backend is running on:

```text
http://127.0.0.1:8000
```

The Vite dev server proxies `/api` requests to the backend.

### Frontend build warning about large chunks

The production build may warn that a JavaScript chunk is larger than 500 kB. This is not currently a blocker. Cytoscape and graph layout libraries add bundle size.

## Build Checks

Frontend production build:

```powershell
cd C:\git\lineage_explorer\frontend
npm run build
```

Backend import check:

```powershell
cd C:\git\lineage_explorer
python -c "from backend.app.main import app; print(app.title)"
```
