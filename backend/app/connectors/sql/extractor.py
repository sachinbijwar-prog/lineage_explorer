import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SqlExtractor:
    """
    Extracts SQL script files from a target directory.
    """

    def __init__(self, directory_path: str = None):
        if not directory_path:
            # Default to sql_samples in the project root
            self.directory_path = Path("sql_samples")
        else:
            self.directory_path = Path(directory_path)

    def extract(self) -> list[dict]:
        """
        Reads all SQL files in the target directory and returns a list of dictionaries
        with keys: 'filename', 'path', and 'content'.
        """
        scripts = []
        if not self.directory_path.exists():
            logger.warning(f"SQL Directory {self.directory_path.absolute()} does not exist.")
            return []

        for file_path in self.directory_path.glob("*.sql"):
            if file_path.is_file():
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    scripts.append({
                        "filename": file_path.name,
                        "path": str(file_path.absolute()),
                        "content": content
                    })
                except Exception as e:
                    logger.error(f"Error reading SQL file {file_path}: {e}")
        return scripts
