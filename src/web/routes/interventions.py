from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Query, status
from src.models.api_schemas import (
    InterventionCreateRequest,
    ReassessmentLinkRequest,
    ReassessmentLinkResponse,
)
from src.services.intervention_service import InterventionService

router = APIRouter(prefix="/api", tags=["Interventions & Reassessment"])


@router.get("/interventions", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
def list_interventions(
    request: Request,
    student_id: Optional[str] = Query(None, description="Filter by pseudonymous student ID")
):
    intervention_service: InterventionService = request.app.state.intervention_service
    return intervention_service.list_interventions(student_id=student_id)


@router.post("/interventions", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_intervention(
    request: Request,
    payload: InterventionCreateRequest
):
    intervention_service: InterventionService = request.app.state.intervention_service
    try:
        result = intervention_service.create_intervention(payload)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the intervention record."
        )


@router.post("/reassessment", response_model=ReassessmentLinkResponse, status_code=status.HTTP_200_OK)
def link_reassessment(
    request: Request,
    payload: ReassessmentLinkRequest
):
    intervention_service: InterventionService = request.app.state.intervention_service
    response = intervention_service.link_reassessment(payload)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.message
        )
    return response
