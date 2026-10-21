from fastapi import APIRouter, Request, status
from src.models.api_schemas import HealthResponse

router = APIRouter(prefix="/api", tags=["System Health"])


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def get_health(request: Request):
    db = request.app.state.db
    try:
        counts = db.get_counts()
        db_status = "connected"
        app_status = "healthy"
    except Exception:
        counts = {}
        db_status = "disconnected"
        app_status = "degraded"

    return HealthResponse(
        status=app_status,
        database=db_status,
        version="0.3.0-phase3",
        counts=counts
    )
