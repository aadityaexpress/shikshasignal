from typing import List, Optional
from fastapi import APIRouter, Request, HTTPException, Query, status
from src.models.api_schemas import StudentSummary, StudentProfileResponse
from src.models.schemas import TeacherActionCard
from src.services.student_service import StudentService

router = APIRouter(prefix="/api/students", tags=["Teacher Decision Support"])


@router.get("", response_model=List[StudentSummary], status_code=status.HTTP_200_OK)
def get_students(
    request: Request,
    grade: Optional[int] = Query(None, ge=1, le=3, description="Filter by grade level (1, 2, or 3)"),
    search: Optional[str] = Query(None, description="Search by student_id or school_id"),
    status_filter: Optional[str] = Query(None, description="Filter by status: priority_for_teacher_review, needs_teacher_review, on_track, insufficient_data")
):
    student_service: StudentService = request.app.state.student_service
    return student_service.list_students(grade=grade, search=search, status_filter=status_filter)


@router.get("/{student_id}", response_model=StudentProfileResponse, status_code=status.HTTP_200_OK)
def get_student_profile(request: Request, student_id: str):
    student_service: StudentService = request.app.state.student_service
    profile = student_service.get_student_profile(student_id.strip())
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID '{student_id}' was not found in the student roster."
        )
    return profile


@router.get("/{student_id}/actions", response_model=List[TeacherActionCard], status_code=status.HTTP_200_OK)
def get_student_actions(request: Request, student_id: str):
    student_service: StudentService = request.app.state.student_service
    actions = student_service.get_student_actions(student_id.strip())
    if actions is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID '{student_id}' was not found."
        )
    return actions
