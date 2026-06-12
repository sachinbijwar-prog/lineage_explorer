from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class NodeType(StrEnum):
    TABLE = "TABLE"
    SQL_SCRIPT = "SQL_SCRIPT"
    SHELL_SCRIPT = "SHELL_SCRIPT"
    CRON_JOB = "CRON_JOB"


class RelationshipType(StrEnum):
    CRON_TRIGGERS = "CRON_TRIGGERS"
    SHELL_EXECUTES = "SHELL_EXECUTES"
    SQL_READS = "SQL_READS"
    SQL_WRITES = "SQL_WRITES"
    DEPENDS_ON = "DEPENDS_ON"


class FileMetadata(BaseModel):
    path: Path
    relative_path: str
    name: str
    suffix: str


class MetadataNode(BaseModel):
    id: str
    name: str
    type: NodeType
    path: str | None = None


class MetadataEdge(BaseModel):
    source: str
    target: str
    relationship: RelationshipType


class MetadataGraph(BaseModel):
    nodes: list[MetadataNode] = Field(default_factory=list)
    edges: list[MetadataEdge] = Field(default_factory=list)


class SqlScanResult(BaseModel):
    sql_file: FileMetadata
    source_tables: list[str] = Field(default_factory=list)
    target_tables: list[str] = Field(default_factory=list)


class ShellScanResult(BaseModel):
    shell_file: FileMetadata
    sql_references: list[str] = Field(default_factory=list)


class CronScanResult(BaseModel):
    cron_file: FileMetadata
    shell_references: list[str] = Field(default_factory=list)


class DdlScanResult(BaseModel):
    ddl_file: FileMetadata
    tables: list[str] = Field(default_factory=list)


class ScanSummary(BaseModel):
    status: str
    tables: int
    sql_files: int
    shell_scripts: int
    cron_jobs: int
    relationships: int
    loaded_to_neo4j: bool
    errors: list[str] = Field(default_factory=list)


class ScanRequest(BaseModel):
    path: str
    load_to_neo4j: bool = True
