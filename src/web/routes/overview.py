from fastapi import APIRouter, Request, status
from src.models.api_schemas import OverviewResponse
from src.services.overview_service import OverviewService

router = APIRouter(prefix="/api", tags=["Overview Metrics"])


@router.get("/overview", response_model=OverviewResponse, status_code=status.HTTP_200_OK)
def get_overview(request: Request):
    overview_service: OverviewService = request.app.state.overview_service
    return overview_service.get_overview()
