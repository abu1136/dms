import os
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.auth.security import get_current_active_user
from app.config import get_settings
from app.database.session import get_db
from app.models.document import Document
from app.models.document_template import DocumentTemplate
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentFilter
from app.services.audit import AuditService
from app.services.document_number import DocumentNumberService
from app.services.pdf_generator import PDFGeneratorService

settings = get_settings()

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document_data: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new document with PDF generation."""
    # Get content from document_data (should include content field)
    content = getattr(document_data, 'content', 'This is a sample document content.')
    
    # Get template if specified
    template_path = None
    if document_data.template_id:
        template = db.query(DocumentTemplate).filter(
            DocumentTemplate.id == document_data.template_id
        ).first()
        if template:
            template_path = template.file_path
    
    # Generate document number
    doc_number = DocumentNumberService.generate_document_number(db)
    
    # Generate PDF with template
    pdf_bytes = PDFGeneratorService.generate_document_pdf(
        document_number=doc_number,
        title=document_data.title,
        content=content,
        requested_by=current_user.username,
        template_path=template_path,
    )
    
    # Save PDF to storage
    file_name = f"{doc_number}.pdf"
    file_path = os.path.join(settings.storage_dir, file_name)
    PDFGeneratorService.save_pdf(pdf_bytes, file_path)
    
    # Create document record
    new_document = Document(
        document_number=doc_number,
        title=document_data.title,
        template_id=document_data.template_id,
        requested_by_id=current_user.id,
        file_path=file_path,
        file_name=file_name,
    )
    db.add(new_document)
    db.commit()
    db.refresh(new_document)
    
    # Log document creation
    AuditService.log_action(
        db,
        current_user.id,
        "DOCUMENT_CREATED",
        document_id=new_document.id,
        details=f"Created document: {doc_number}"
    )
    
    return new_document


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    created_by: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
):
    """List documents. Admins see all, users see only their own."""
    query = db.query(Document)
    
    # Role-based filtering
    if current_user.role != 'admin':
        query = query.filter(Document.requested_by_id == current_user.id)
    else:
        # Admin-only filters
        if created_by:
            query = query.filter(Document.requested_by_id == created_by)
        
        # Date filtering with proper timezone handling
        from datetime import datetime, time, timedelta
        import pytz

        local_tz = pytz.timezone("Asia/Kolkata")

        if date_from:
            date_from_date = datetime.fromisoformat(date_from).date()
            start_local = local_tz.localize(datetime.combine(date_from_date, time.min))
            start_utc = start_local.astimezone(pytz.utc).replace(tzinfo=None)
            query = query.filter(Document.created_at >= start_utc)

        if date_to:
            date_to_date = datetime.fromisoformat(date_to).date()
            # Include the entire to_date by adding 1 day and using <
            end_local = local_tz.localize(datetime.combine(date_to_date + timedelta(days=1), time.min))
            end_utc = end_local.astimezone(pytz.utc).replace(tzinfo=None)
            query = query.filter(Document.created_at < end_utc)
    
    # Order by created_at DESC (latest first)
    query = query.order_by(Document.created_at.desc())
    
    documents = query.offset(skip).limit(limit).all()
    return documents


@router.get("/search", response_model=List[DocumentResponse])
async def search_documents(
    document_number: str | None = None,
    title: str | None = None,
    user_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Search and filter documents."""
    query = db.query(Document)
    
    if document_number:
        query = query.filter(Document.document_number.contains(document_number))
    
    if title:
        query = query.filter(Document.title.contains(title))
    
    if user_id:
        query = query.filter(Document.requested_by_id == user_id)
    
    documents = query.all()
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific document by ID."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Log document access
    AuditService.log_action(
        db,
        current_user.id,
        "DOCUMENT_VIEWED",
        document_id=document.id,
        details=f"Viewed document: {document.document_number}"
    )
    
    return document


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download a document PDF."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found"
        )
    
    # Log document download
    AuditService.log_action(
        db,
        current_user.id,
        "DOCUMENT_DOWNLOADED",
        document_id=document.id,
        details=f"Downloaded document: {document.document_number}"
    )
    
    return FileResponse(
        path=document.file_path,
        media_type=document.mime_type,
        filename=document.file_name
    )
