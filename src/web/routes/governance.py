from typing import Optional
from fastapi import APIRouter, Request, Query, status
from src.models.api_schemas import ValidationLogsResponse
from src.models.database import DatabaseManager

router = APIRouter(prefix="/api", tags=["Governance & Data Quality"])


@router.get("/validation-logs", response_model=ValidationLogsResponse, status_code=status.HTTP_200_OK)
def get_validation_logs(
    request: Request,
    limit: int = Query(100, ge=1, le=1000, description="Max logs to retrieve"),
    status: Optional[str] = Query(None, description="Filter by status: valid, warning, rejected")
):
    db: DatabaseManager = request.app.state.db
    logs = db.get_validation_logs(limit=limit, status=status)
    return ValidationLogsResponse(
        total_count=len(logs),
        logs=logs
    )
