from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.services.lineage_service import LineageService

router = APIRouter()


class IngestionResponse(BaseModel):
    nodes_created: int
    relationships_created: int


class SQLIngestionRequest(BaseModel):
    directory_path: str | None = None


@router.post("/api/ingestion/sql", response_model=IngestionResponse)
@router.post("/api/v1/ingestion/sql", response_model=IngestionResponse)
def ingest_sql(payload: SQLIngestionRequest = None):
    """
    POST /api/ingestion/sql and POST /api/v1/ingestion/sql
    Reads all SQL files, parses them, and loads them into Neo4j.
    """
    try:
        dir_path = payload.directory_path if payload else None
        result = LineageService.ingest_sql_directory(dir_path)
        return IngestionResponse(
            nodes_created=result.get("nodes_created", 0),
            relationships_created=result.get("relationships_created", 0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQL Ingestion failed: {e}")


@router.get("/api/lineage/graph")
@router.get("/api/v1/lineage/graph")
def get_graph():
    """
    GET /api/lineage/graph and GET /api/v1/lineage/graph
    Returns the complete lineage graph in Cytoscape-compatible format.
    """
    try:
        return LineageService.get_lineage_graph()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch lineage graph: {e}")


@router.get("/api/lineage/upstream/{node}")
@router.get("/api/v1/lineage/upstream/{node}")
def get_upstream_lineage(node: str):
    """
    GET /api/lineage/upstream/{node} and GET /api/v1/lineage/upstream/{node}
    Returns all upstream dependencies contributing to the target node.
    """
    try:
        return LineageService.get_upstream(node)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch upstream lineage: {e}")


@router.get("/api/lineage/downstream/{node}")
@router.get("/api/v1/lineage/downstream/{node}")
def get_downstream_lineage(node: str):
    """
    GET /api/lineage/downstream/{node} and GET /api/v1/lineage/downstream/{node}
    Returns all downstream dependencies impacted by the target node.
    """
    try:
        return LineageService.get_downstream(node)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch downstream lineage: {e}")


class InformaticaIngestionRequest(BaseModel):
    directory_path: str | None = None


@router.post("/api/ingestion/informatica", response_model=IngestionResponse)
@router.post("/api/v1/ingestion/informatica", response_model=IngestionResponse)
def ingest_informatica(payload: InformaticaIngestionRequest = None):
    """
    POST /api/ingestion/informatica and POST /api/v1/ingestion/informatica
    Reads all Informatica XML files, parses them, and loads them into Neo4j.
    """
    try:
        dir_path = payload.directory_path if payload else None
        result = LineageService.ingest_informatica_directory(dir_path)
        return IngestionResponse(
            nodes_created=result.get("nodes_created", 0),
            relationships_created=result.get("relationships_created", 0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Informatica Ingestion failed: {e}")
