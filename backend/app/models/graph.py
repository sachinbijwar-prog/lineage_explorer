from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Node models
# ---------------------------------------------------------------------------

class NodeData(BaseModel):
    """Properties carried by every graph node."""
    id: str
    type: str = "Unknown"
    role: str | None = None         # "origin" | "impacted" — populated by impact analysis
    description: str | None = None
    owner: str | None = None
    system: str | None = None

class NodeMetadataUpdate(BaseModel):
    """Properties that can be updated dynamically via API-03."""
    description: str | None = None
    owner: str | None = None
    system: str | None = None


class GraphNode(BaseModel):
    """Cytoscape-compatible node envelope."""
    data: NodeData


# ---------------------------------------------------------------------------
# Edge models
# ---------------------------------------------------------------------------

class EdgeData(BaseModel):
    """Properties carried by every graph edge."""
    source: str
    target: str
    relationship: str


class GraphEdge(BaseModel):
    """Cytoscape-compatible edge envelope."""
    data: EdgeData


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class LineageResponse(BaseModel):
    """
    Standard response for lineage queries (upstream / downstream / unified).
    """
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class ImpactSummary(BaseModel):
    """Metadata block returned by impact analysis."""
    affected_node_count: int
    impact_depth: int


class ImpactResponse(BaseModel):
    """
    Response for impact analysis queries.
    Extends LineageResponse with origin node identification and impact metadata.
    """
    origin_node: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    impact_summary: ImpactSummary


# ---------------------------------------------------------------------------
# Upload / Ingestion models
# ---------------------------------------------------------------------------

class UploadNode(BaseModel):
    """Represents a node in an ingestion payload."""
    id: str
    type: str
    description: str | None = None
    owner: str | None = None
    system: str | None = None


class UploadEdge(BaseModel):
    """Represents a relationship edge in an ingestion payload."""
    source: str
    target: str
    relationship_type: str


class UploadGraphPayload(BaseModel):
    """Root model for graph ingestion payloads via the API."""
    nodes: list[UploadNode] = []
    edges: list[UploadEdge] = []
