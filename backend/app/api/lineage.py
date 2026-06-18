from fastapi import APIRouter, Query

from backend.app.models.graph import ImpactResponse, LineageResponse, UploadGraphPayload
from backend.app.services.graph_service import GraphService

router = APIRouter()


@router.get("/api/v1/lineage/test")
def test_graph():
    status = GraphService.test_connection()
    return {
        "neo4j_status": status
    }


@router.post("/api/v1/lineage/seed")
def seed_graph():
    result = GraphService.seed_demo_graph()
    return {
        "status": result
    }


@router.post("/api/v1/lineage/upload")
def upload_graph(payload: UploadGraphPayload):
    """
    API-01: JSON Payload Ingestion API.
    Allows bulk uploading of nodes and relationships to update the lineage graph.
    """
    return GraphService.upload_graph(payload)


@router.get("/api/v1/lineage/validate")
def validate_graph():
    """
    Validates the graph health.
    Returns counts of orphaned nodes and cyclic paths.
    """
    return GraphService.validate_graph()


@router.get("/api/v1/lineage/nodes", response_model=list)
def get_all_nodes():
    """
    Returns all nodes in the database.
    """
    return GraphService.get_all_nodes()


@router.get("/api/v1/lineage/search", response_model=list)
def search_nodes(q: str = Query(..., min_length=1, description="Search query"), limit: int = Query(20, ge=1, le=100)):
    """
    UI-06: Search Functionality
    Search for nodes by name, type, description, owner, or system.
    Returns a list of matching nodes with their basic info.
    """
    return GraphService.search_nodes(query=q, limit=limit)


@router.get("/api/v1/lineage/upstream/{node_id}", response_model=LineageResponse)
def get_upstream_lineage(node_id: str, depth: int = Query(10, ge=1, le=50)):
    return GraphService.get_upstream_lineage(node_id, max_depth=depth)


@router.get("/api/v1/lineage/downstream/{node_id}", response_model=LineageResponse)
def get_downstream_lineage(node_id: str, depth: int = Query(10, ge=1, le=50)):
    return GraphService.get_downstream_lineage(node_id, max_depth=depth)


@router.get("/api/v1/lineage/impact/{node_id}", response_model=ImpactResponse)
def get_impact_analysis(node_id: str, depth: int = Query(10, ge=1, le=50)):
    """
    Impact Analysis endpoint.

    Returns all downstream nodes impacted if the given node changes or fails.
    Includes impact_summary with affected_node_count and impact_depth.
    """
    return GraphService.get_impact_analysis(node_id, max_depth=depth)


@router.get("/api/v1/lineage/{node_id}", response_model=LineageResponse)
def get_lineage(node_id: str, direction: str = "both", depth: int = Query(10, ge=1, le=50)):
    """
    Unified lineage endpoint.

    direction: upstream | downstream | both (default)
    depth:     max hops to traverse (default 10)
    """
    return GraphService.get_lineage(node_id, direction=direction, max_depth=depth)
