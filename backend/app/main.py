from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.health import router as health_router
from backend.app.api.lineage import router as lineage_router
from backend.app.api.impact import router as impact_router
from backend.app.api.node import router as node_router
from backend.app.api.path import router as path_router
from backend.app.api.scan import router as scan_router
from backend.app.api.lineage_ingestion import router as lineage_ingestion_router
from backend.app.services.graph_service import GraphService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    print("Initializing Neo4j database indexes...")
    try:
        GraphService.init_db()
        print("Database indexes initialized.")
    except Exception as e:
        print(f"Warning: Failed to initialize indexes: {e}")
    yield
    # Shutdown tasks
    pass


app = FastAPI(
    title="Enterprise Dependency & Lineage Explorer",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(lineage_router)
app.include_router(impact_router)
app.include_router(node_router)
app.include_router(path_router)
app.include_router(scan_router)
app.include_router(lineage_ingestion_router)

@app.get("/")
def root():
    return {
        "message": "Enterprise Dependency & Lineage Explorer"
    }
