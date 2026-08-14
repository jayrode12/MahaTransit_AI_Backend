import math
from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.complaint import (
    AttachmentTypeLiteral,
    ComplaintCreate,
    ComplaintUpdate,
    ComplaintResponse,
    ComplaintListResponse,
    ComplaintRemarkCreate,
    ComplaintRemarkResponse,
    ComplaintAttachmentCreate,
    ComplaintAttachmentResponse,
)
from app.services.complaint_service import ComplaintService
from app.services.storage_service import StorageService

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post(
    "",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new public transport complaint",
)
def create_complaint(
    complaint_in: ComplaintCreate,
    db: Session = Depends(get_db),
):
    """
    Creates a new complaint for Metro, BEST Bus, or Local Trains.
    Generates a unique ticket number, records initial remarks, and attaches any files.
    """
    return ComplaintService.create_complaint(db=db, complaint_in=complaint_in)


@router.get(
    "",
    response_model=ComplaintListResponse,
    summary="Get list of complaints with search, filters and pagination",
)
def list_complaints(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status: submitted, in_progress, resolved, closed, rejected"),
    priority: Optional[str] = Query(None, description="Filter by priority: low, medium, high, critical"),
    transit_mode: Optional[str] = Query(None, description="Filter by transit mode: metro, bus, train"),
    department_id: Optional[UUID] = Query(None, description="Filter by department UUID"),
    category_id: Optional[UUID] = Query(None, description="Filter by category UUID"),
    citizen_id: Optional[UUID] = Query(None, description="Filter by citizen UUID"),
    search: Optional[str] = Query(None, description="Search keyword across title, description, and ticket number"),
    db: Session = Depends(get_db),
):
    """
    Retrieves paginated complaints with keyword search and multi-attribute filters.
    """
    skip = (page - 1) * limit
    complaints, total = ComplaintService.get_complaints(
        db=db,
        skip=skip,
        limit=limit,
        citizen_id=citizen_id,
        department_id=department_id,
        category_id=category_id,
        status=status,
        priority=priority,
        transit_mode=transit_mode,
        search=search,
    )
    pages = math.ceil(total / limit) if total > 0 else 1
    return {
        "items": complaints,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


@router.get(
    "/track/{ticket_number}",
    response_model=ComplaintResponse,
    summary="Public tracking of complaint by ticket number",
)
def track_complaint(
    ticket_number: str,
    db: Session = Depends(get_db),
):
    """
    Allows citizens to track complaint status using their unique ticket number (e.g. MT-MET-202608-XXXX).
    """
    complaint = ComplaintService.get_complaint_by_ticket_number(db=db, ticket_number=ticket_number.strip())
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ticket number '{ticket_number}' not found.",
        )
    return complaint


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    summary="Get complaint details by ID",
)
def get_complaint(
    complaint_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Retrieves full complaint details including attachments and timeline remarks.
    """
    complaint = ComplaintService.get_complaint_by_id(db=db, complaint_id=complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ID '{complaint_id}' not found.",
        )
    return complaint


@router.get(
    "/{complaint_id}/timeline",
    response_model=list[ComplaintRemarkResponse],
    summary="Get complaint timeline audit history",
)
def get_complaint_timeline(
    complaint_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Retrieves the chronological status change and remarks audit history for a complaint.
    """
    timeline = ComplaintService.get_timeline(db=db, complaint_id=complaint_id)
    if timeline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ID '{complaint_id}' not found.",
        )
    return timeline


@router.patch(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    summary="Update complaint status, priority, or remarks",
)
def update_complaint(
    complaint_id: UUID,
    complaint_in: ComplaintUpdate,
    db: Session = Depends(get_db),
):
    """
    Updates complaint status, priority, or adds resolution remarks.
    Automatically records timeline history.
    """
    updated = ComplaintService.update_complaint(db=db, complaint_id=complaint_id, complaint_in=complaint_in)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ID '{complaint_id}' not found.",
        )
    return updated


@router.post(
    "/{complaint_id}/remarks",
    response_model=ComplaintRemarkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an officer remark to complaint timeline",
)
def add_remark(
    complaint_id: UUID,
    remark_in: ComplaintRemarkCreate,
    db: Session = Depends(get_db),
):
    """
    Adds a remark / timeline note to a specific complaint.
    """
    remark = ComplaintService.add_remark(db=db, complaint_id=complaint_id, remark_in=remark_in)
    if not remark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ID '{complaint_id}' not found.",
        )
    return remark


@router.post(
    "/{complaint_id}/upload-attachment",
    response_model=ComplaintAttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file (Audio -> 'voice-files', Images/Docs -> 'attachments')",
)
async def upload_attachment(
    complaint_id: UUID,
    file: UploadFile = File(..., description="Audio voice note, photo, or document"),
    attachment_type: Optional[AttachmentTypeLiteral] = Form(None, description="Optional override: audio, image, video, document"),
    db: Session = Depends(get_db),
):
    """
    Uploads a file directly to Supabase Storage:
    - Audio voice notes (.mp3, .wav, .m4a, .ogg) -> stored in 'voice-files' bucket
    - Images (.jpg, .png) and Documents (.pdf, text) -> stored in 'attachments' bucket
    - Links the resulting public URL to the complaint.
    """
    complaint = ComplaintService.get_complaint_by_id(db=db, complaint_id=complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ID '{complaint_id}' not found.",
        )

    file_bytes = await file.read()
    file_size = len(file_bytes)

    public_url, detected_type, _ = StorageService.upload_file(
        file_bytes=file_bytes,
        file_name=file.filename or "attachment",
        mime_type=file.content_type,
        complaint_id=complaint_id,
        forced_attachment_type=attachment_type,
    )

    attachment_in = ComplaintAttachmentCreate(
        attachment_type=detected_type,
        file_name=file.filename or "attachment",
        file_url=public_url,
        mime_type=file.content_type,
        file_size=file_size,
    )
    return ComplaintService.add_attachment(db=db, complaint_id=complaint_id, attachment_in=attachment_in)


@router.post(
    "/{complaint_id}/attachments",
    response_model=ComplaintAttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an attachment metadata record to complaint",
)
def add_attachment(
    complaint_id: UUID,
    attachment_in: ComplaintAttachmentCreate,
    db: Session = Depends(get_db),
):
    """
    Links an existing attachment URL to the complaint.
    """
    attachment = ComplaintService.add_attachment(db=db, complaint_id=complaint_id, attachment_in=attachment_in)
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ID '{complaint_id}' not found.",
        )
    return attachment


@router.delete(
    "/{complaint_id}",
    summary="Delete a complaint",
)
def delete_complaint(
    complaint_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Deletes a complaint and cascades associated records.
    """
    success = ComplaintService.delete_complaint(db=db, complaint_id=complaint_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ID '{complaint_id}' not found.",
        )
    return {"message": "Complaint deleted successfully", "id": complaint_id}
