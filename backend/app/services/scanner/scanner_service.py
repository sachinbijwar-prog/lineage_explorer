import logging
from pathlib import Path

from backend.app.services.scanner.cron_scanner import CronScanner
from backend.app.services.scanner.ddl_scanner import DdlScanner
from backend.app.services.scanner.metadata_builder import MetadataBuilder
from backend.app.services.scanner.models import FileMetadata, ScanSummary
from backend.app.services.scanner.neo4j_loader import Neo4jMetadataLoader
from backend.app.services.scanner.shell_scanner import ShellScanner
from backend.app.services.scanner.sql_scanner import SqlScanner

logger = logging.getLogger(__name__)


class ScannerService:
    def __init__(self, loader: Neo4jMetadataLoader | None = None):
        self.cron_scanner = CronScanner()
        self.shell_scanner = ShellScanner()
        self.sql_scanner = SqlScanner()
        self.ddl_scanner = DdlScanner()
        self.loader = loader or Neo4jMetadataLoader()

    def scan_directory(self, path: str, load_to_neo4j: bool = True) -> ScanSummary:
        root = Path(path).expanduser().resolve()
        errors: list[str] = []

        if not root.exists():
            raise FileNotFoundError(f"Scan path does not exist: {root}")
        if not root.is_dir():
            raise NotADirectoryError(f"Scan path is not a directory: {root}")

        files = self.discover_files(root)
        if not files:
            return ScanSummary(
                status="empty",
                tables=0,
                sql_files=0,
                shell_scripts=0,
                cron_jobs=0,
                relationships=0,
                loaded_to_neo4j=False,
                errors=["No .sql, .sh, or .cron files found"],
            )

        ddl_files = [file for file in files if self.is_under(file, "ddl") and file.suffix == ".sql"]
        sql_files = [file for file in files if self.is_under(file, "sql") and file.suffix == ".sql"]
        shell_files = [file for file in files if file.suffix == ".sh"]
        cron_files = [file for file in files if file.suffix == ".cron"]

        ddl_results, ddl_errors = self.ddl_scanner.scan(ddl_files)
        sql_results, sql_errors = self.sql_scanner.scan(sql_files)
        shell_results, shell_errors = self.shell_scanner.scan(shell_files)
        cron_results, cron_errors = self.cron_scanner.scan(cron_files)
        errors.extend(ddl_errors + sql_errors + shell_errors + cron_errors)

        graph = MetadataBuilder(files).build(
            ddl_results=ddl_results,
            sql_results=sql_results,
            shell_results=shell_results,
            cron_results=cron_results,
        )

        loaded = False
        if load_to_neo4j:
            try:
                self.loader.load(graph.nodes, graph.edges)
                loaded = True
            except Exception as exc:
                message = f"Failed to load metadata graph into Neo4j: {exc}"
                logger.exception(message)
                errors.append(message)

        return ScanSummary(
            status="success" if not errors else "partial_success",
            tables=sum(1 for node in graph.nodes if node.type == "TABLE"),
            sql_files=sum(1 for node in graph.nodes if node.type == "SQL_SCRIPT"),
            shell_scripts=sum(1 for node in graph.nodes if node.type == "SHELL_SCRIPT"),
            cron_jobs=sum(1 for node in graph.nodes if node.type == "CRON_JOB"),
            relationships=len(graph.edges),
            loaded_to_neo4j=loaded,
            errors=errors,
        )

    def discover_files(self, root: Path) -> list[FileMetadata]:
        discovered: list[FileMetadata] = []
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".cron", ".sh", ".sql"}:
                continue
            discovered.append(
                FileMetadata(
                    path=path,
                    relative_path=path.relative_to(root).as_posix(),
                    name=path.name,
                    suffix=path.suffix.lower(),
                )
            )
        return sorted(discovered, key=lambda file: file.relative_path)

    @staticmethod
    def is_under(file: FileMetadata, directory: str) -> bool:
        return file.relative_path.lower().startswith(f"{directory.lower()}/")
