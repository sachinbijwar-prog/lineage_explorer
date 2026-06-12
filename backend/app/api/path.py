from fastapi import APIRouter, HTTPException, Query
from ..services.graph_service import GraphService

router = APIRouter(prefix="/api/v1/path", tags=["Path"])

@router.get("/{source_id}/{target_id}")
async def get_path(source_id: str, target_id: str, depth: int = Query(10, ge=1, le=50)):
    """
    Return the shortest path between source and target nodes.
    """
    try:
        path = GraphService.find_shortest_path(source_id, target_id, depth)
        return {"path": path}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
