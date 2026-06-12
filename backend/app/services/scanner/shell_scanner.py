import logging
import re
from pathlib import PurePosixPath

from backend.app.services.scanner.models import FileMetadata, ShellScanResult

logger = logging.getLogger(__name__)


class ShellScanner:
    SQL_FILE_RE = re.compile(r"([A-Za-z0-9_./${}\-]+\.sql)")
    EXECUTION_RE = re.compile(r"\b(?:beeline|hive|spark-sql)\b.*?\s-f\s+['\"]?([^'\"\s]+\.sql)", re.IGNORECASE)

    def scan(self, shell_files: list[FileMetadata]) -> tuple[list[ShellScanResult], list[str]]:
        results: list[ShellScanResult] = []
        errors: list[str] = []

        for file in shell_files:
            try:
                text = file.path.read_text(encoding="utf-8", errors="ignore")
                references = set(self.EXECUTION_RE.findall(text))
                references.update(self.SQL_FILE_RE.findall(text))
                results.append(
                    ShellScanResult(
                        shell_file=file,
                        sql_references=sorted(self.clean_reference(reference) for reference in references),
                    )
                )
            except OSError as exc:
                message = f"Failed to read shell file {file.relative_path}: {exc}"
                logger.warning(message)
                errors.append(message)

        return results, errors

    @staticmethod
    def clean_reference(reference: str) -> str:
        return PurePosixPath(reference.replace("\\", "/")).name
