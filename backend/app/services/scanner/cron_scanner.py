import logging
import re
from pathlib import PurePosixPath

from backend.app.services.scanner.models import CronScanResult, FileMetadata

logger = logging.getLogger(__name__)


class CronScanner:
    SHELL_FILE_RE = re.compile(r"([A-Za-z0-9_./${}\-]+\.sh)")

    def scan(self, cron_files: list[FileMetadata]) -> tuple[list[CronScanResult], list[str]]:
        results: list[CronScanResult] = []
        errors: list[str] = []

        for file in cron_files:
            try:
                references: set[str] = set()
                for line in file.path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#") or "=" in stripped.split(" ", 1)[0]:
                        continue
                    references.update(self.SHELL_FILE_RE.findall(stripped))

                results.append(
                    CronScanResult(
                        cron_file=file,
                        shell_references=sorted(self.clean_reference(reference) for reference in references),
                    )
                )
            except OSError as exc:
                message = f"Failed to read cron file {file.relative_path}: {exc}"
                logger.warning(message)
                errors.append(message)

        return results, errors

    @staticmethod
    def clean_reference(reference: str) -> str:
        return PurePosixPath(reference.replace("\\", "/")).name
