from pathlib import Path

from backend.app.services.scanner.models import (
    CronScanResult,
    DdlScanResult,
    FileMetadata,
    MetadataEdge,
    MetadataGraph,
    MetadataNode,
    NodeType,
    RelationshipType,
    ShellScanResult,
    SqlScanResult,
)


class MetadataBuilder:
    def __init__(self, files: list[FileMetadata]):
        self.files = files
        self._nodes: dict[str, MetadataNode] = {}
        self._edges: set[tuple[str, str, RelationshipType]] = set()
        self._files_by_name: dict[str, FileMetadata] = {file.name: file for file in files}
        self._files_by_stem: dict[str, FileMetadata] = {Path(file.name).stem: file for file in files}

    def build(
        self,
        ddl_results: list[DdlScanResult],
        sql_results: list[SqlScanResult],
        shell_results: list[ShellScanResult],
        cron_results: list[CronScanResult],
    ) -> MetadataGraph:
        for ddl in ddl_results:
            for table in ddl.tables:
                self.add_table(table)

        for sql in sql_results:
            sql_id = self.add_file_node(sql.sql_file, NodeType.SQL_SCRIPT)
            for table in sql.source_tables:
                table_id = self.add_table(table)
                self.add_edge(sql_id, table_id, RelationshipType.SQL_READS)
            for table in sql.target_tables:
                table_id = self.add_table(table)
                self.add_edge(sql_id, table_id, RelationshipType.SQL_WRITES)
                for source_table in sql.source_tables:
                    source_id = self.add_table(source_table)
                    self.add_edge(table_id, source_id, RelationshipType.DEPENDS_ON)

        for shell in shell_results:
            shell_id = self.add_file_node(shell.shell_file, NodeType.SHELL_SCRIPT)
            for sql_reference in shell.sql_references:
                sql_file = self.resolve_file(sql_reference)
                sql_id = self.add_reference_node(sql_reference, sql_file, NodeType.SQL_SCRIPT)
                self.add_edge(shell_id, sql_id, RelationshipType.SHELL_EXECUTES)
                self.add_edge(shell_id, sql_id, RelationshipType.DEPENDS_ON)

        for cron in cron_results:
            cron_id = self.add_file_node(cron.cron_file, NodeType.CRON_JOB)
            for shell_reference in cron.shell_references:
                shell_file = self.resolve_file(shell_reference)
                shell_id = self.add_reference_node(shell_reference, shell_file, NodeType.SHELL_SCRIPT)
                self.add_edge(cron_id, shell_id, RelationshipType.CRON_TRIGGERS)
                self.add_edge(cron_id, shell_id, RelationshipType.DEPENDS_ON)

        return MetadataGraph(
            nodes=sorted(self._nodes.values(), key=lambda node: (node.type, node.name)),
            edges=[
                MetadataEdge(source=source, target=target, relationship=relationship)
                for source, target, relationship in sorted(self._edges)
            ],
        )

    def add_table(self, table_name: str) -> str:
        clean_name = self.normalize_table_name(table_name)
        node_id = f"TABLE:{clean_name}"
        self._nodes.setdefault(
            node_id,
            MetadataNode(id=node_id, name=clean_name, type=NodeType.TABLE),
        )
        return node_id

    def add_file_node(self, file: FileMetadata, node_type: NodeType) -> str:
        node_id = f"{node_type}:{file.relative_path}"
        self._nodes.setdefault(
            node_id,
            MetadataNode(id=node_id, name=file.name, type=node_type, path=file.relative_path),
        )
        return node_id

    def add_reference_node(
        self,
        reference: str,
        file: FileMetadata | None,
        node_type: NodeType,
    ) -> str:
        if file:
            return self.add_file_node(file, node_type)

        name = Path(reference).name
        node_id = f"{node_type}:{name}"
        self._nodes.setdefault(
            node_id,
            MetadataNode(id=node_id, name=name, type=node_type, path=reference),
        )
        return node_id

    def add_edge(self, source: str, target: str, relationship: RelationshipType) -> None:
        self._edges.add((source, target, relationship))

    def resolve_file(self, reference: str) -> FileMetadata | None:
        reference_path = Path(reference)
        name = reference_path.name
        if name in self._files_by_name:
            return self._files_by_name[name]
        return self._files_by_stem.get(reference_path.stem)

    @staticmethod
    def normalize_table_name(table_name: str) -> str:
        return table_name.strip().strip(";").strip('"').strip("`").upper()
