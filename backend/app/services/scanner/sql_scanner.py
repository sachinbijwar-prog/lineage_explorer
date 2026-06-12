import logging
import re

from backend.app.services.scanner.models import FileMetadata, SqlScanResult

logger = logging.getLogger(__name__)


class SqlScanner:
    TARGET_PATTERNS = [
        re.compile(r"\bINSERT\s+OVERWRITE\s+TABLE\s+([A-Z0-9_.$`\"]+)", re.IGNORECASE),
        re.compile(r"\bINSERT\s+INTO\s+(?:TABLE\s+)?([A-Z0-9_.$`\"]+)", re.IGNORECASE),
        re.compile(r"\bCREATE\s+(?:OR\s+REPLACE\s+)?TABLE\s+([A-Z0-9_.$`\"]+)\s+AS\b", re.IGNORECASE),
        re.compile(r"\bMERGE\s+INTO\s+([A-Z0-9_.$`\"]+)", re.IGNORECASE),
    ]
    SOURCE_RE = re.compile(r"\b(?:FROM|JOIN)\s+([A-Z0-9_.$`\"]+)", re.IGNORECASE)
    CTE_RE = re.compile(r"(?:\bWITH|,)\s*([A-Z0-9_.$`\"]+)\s*(?:\([^)]*\))?\s*AS\s*\(", re.IGNORECASE)

    def scan(self, sql_files: list[FileMetadata]) -> tuple[list[SqlScanResult], list[str]]:
        results: list[SqlScanResult] = []
        errors: list[str] = []

        try:
            import sqlparse
        except ImportError:
            message = "Missing dependency 'sqlparse'. Run: pip install -r backend/requirements.txt"
            logger.error(message)
            return [], [message]

        for file in sql_files:
            try:
                text = file.path.read_text(encoding="utf-8", errors="ignore")
                statements = sqlparse.split(text)
                source_tables: set[str] = set()
                target_tables: set[str] = set()

                for statement in statements:
                    normalized = sqlparse.format(statement, strip_comments=True, keyword_case="upper")
                    ctes = self.extract_ctes(normalized)
                    source_tables.update(self.extract_sources(normalized, ctes))
                    target_tables.update(self.extract_targets(normalized))

                results.append(
                    SqlScanResult(
                        sql_file=file,
                        source_tables=sorted(source_tables),
                        target_tables=sorted(target_tables),
                    )
                )
            except Exception as exc:
                message = f"Failed to parse SQL file {file.relative_path}: {exc}"
                logger.warning(message)
                errors.append(message)

        return results, errors

    def extract_targets(self, statement: str) -> set[str]:
        targets: set[str] = set()
        for pattern in self.TARGET_PATTERNS:
            targets.update(self.clean_table_name(match) for match in pattern.findall(statement))
        return targets

    def extract_sources(self, statement: str, ctes: set[str]) -> set[str]:
        return {
            self.clean_table_name(match)
            for match in self.SOURCE_RE.findall(statement)
            if not self.is_subquery_alias(match) and self.clean_table_name(match) not in ctes
        }

    def extract_ctes(self, statement: str) -> set[str]:
        return {
            self.clean_table_name(match)
            for match in self.CTE_RE.findall(statement)
        }

    @staticmethod
    def clean_table_name(value: str) -> str:
        return value.strip().strip(";").strip(",").strip('"').strip("`").upper()

    @staticmethod
    def is_subquery_alias(value: str) -> bool:
        return value.strip().startswith("(")
