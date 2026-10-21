from typing import Optional
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException, status
from src.models.api_schemas import ImportSummaryResponse
from src.services.import_service import ImportService

router = APIRouter(prefix="/api", tags=["Data Ingestion"])


@router.post("/import", response_model=ImportSummaryResponse, status_code=status.HTTP_200_OK)
async def import_csv(
    request: Request,
    file: UploadFile = File(..., description="CSV file to import"),
    file_type: Optional[str] = Form(None, description="Optional entity type: students, assessments, attendance, interventions")
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only .csv files are supported."
        )

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}"
        )

    import_service: ImportService = request.app.state.import_service
    summary = import_service.import_csv_content(
        file_name=file.filename,
        content_bytes=content,
        file_type=file_type
    )

    return summary
