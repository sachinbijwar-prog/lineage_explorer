from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.lineage import router as lineage_router
from app.api.node import router as node_router
from app.services.graph_service import GraphService


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

app.include_router(health_router)
app.include_router(lineage_router)
app.include_router(node_router)

@app.get("/")
def root():
    return {
        "message": "Enterprise Dependency & Lineage Explorer"
    }