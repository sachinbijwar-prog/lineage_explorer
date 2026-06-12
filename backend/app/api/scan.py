from fastapi import APIRouter, HTTPException

from backend.app.services.scanner.models import ScanRequest, ScanSummary
from backend.app.services.scanner.scanner_service import ScannerService

router = APIRouter()


@router.post("/scan", response_model=ScanSummary)
def scan_metadata(request: ScanRequest):
    try:
        return ScannerService().scan_directory(
            request.path,
            load_to_neo4j=request.load_to_neo4j,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except NotADirectoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Metadata scan failed: {exc}") from exc
