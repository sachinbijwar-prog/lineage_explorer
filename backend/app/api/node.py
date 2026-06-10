from fastapi import APIRouter, HTTPException

from backend.app.models.graph import NodeData, NodeMetadataUpdate
from backend.app.services.graph_service import GraphService

router = APIRouter()

@router.get("/api/v1/node/{node_id}", response_model=NodeData)
def get_node_details(node_id: str):
    """
    API-02: Fetch full enriched metadata for a specific graph node.
    """
    node_data = GraphService.get_node_details(node_id)
    if not node_data:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    return node_data

@router.patch("/api/v1/node/{node_id}", response_model=NodeData)
def update_node_metadata(node_id: str, updates: NodeMetadataUpdate):
    """
    API-03: Update specific metadata fields for a node.
    """
    update_dict = updates.model_dump(exclude_unset=True)
    updated_node = GraphService.update_node_metadata(node_id, update_dict)
    if not updated_node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    return updated_node
