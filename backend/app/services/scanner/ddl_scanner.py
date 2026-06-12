import logging
import re

from backend.app.services.scanner.models import DdlScanResult, FileMetadata

logger = logging.getLogger(__name__)


class DdlScanner:
    CREATE_TABLE_RE = re.compile(
        r"\bCREATE\s+(?:EXTERNAL\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Z0-9_.$`\"]+)",
        re.IGNORECASE,
    )

    def scan(self, ddl_files: list[FileMetadata]) -> tuple[list[DdlScanResult], list[str]]:
        results: list[DdlScanResult] = []
        errors: list[str] = []

        for file in ddl_files:
            try:
                text = file.path.read_text(encoding="utf-8", errors="ignore")
                tables = [self.clean_table_name(match) for match in self.CREATE_TABLE_RE.findall(text)]
                results.append(DdlScanResult(ddl_file=file, tables=sorted(set(tables))))
            except OSError as exc:
                message = f"Failed to read DDL file {file.relative_path}: {exc}"
                logger.warning(message)
                errors.append(message)

        return results, errors

    @staticmethod
    def clean_table_name(value: str) -> str:
        return value.strip().strip(";").strip('"').strip("`").upper()
