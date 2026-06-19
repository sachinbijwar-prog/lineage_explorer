from enum import Enum
from pydantic import BaseModel


class NodeTypes(str, Enum):
    TABLE = "TABLE"
    VIEW = "VIEW"
    PROCEDURE = "PROCEDURE"
    SCRIPT = "SCRIPT"
    WORKFLOW = "WORKFLOW"
    JOB = "JOB"
    MAPPING = "MAPPING"
    TRANSFORMATION = "TRANSFORMATION"
    FILE = "FILE"


class Node(BaseModel):
    id: str
    name: str
    type: NodeTypes
    source_system: str


class Relationship(BaseModel):
    source: str
    target: str
    relationship_type: str


class LineageGraph(BaseModel):
    nodes: list[Node] = []
    relationships: list[Relationship] = []
