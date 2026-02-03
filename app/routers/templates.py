from typing import List
import uuid
import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.auth.security import require_admin, get_current_active_user
from app.database.session import get_db
from app.models.document_template import DocumentTemplate
from app.models.user import User
from app.schemas.template import DocumentTemplateResponse
from app.services.template import TemplateService
from app.services.audit import AuditService
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/templates", tags=["Templates"])

# Maximum file size: 50MB
MAX_FILE_SIZE = 50 * 1024 * 1024


@router.post("/upload", response_model=DocumentTemplateResponse, status_code=status.HTTP_201_CREATED)
async def upload_template(
    name: str = Form(...),
    description: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Upload a new document template (admin only)."""
    # Validate PDF file by content type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Check if template name already exists
    existing_template = db.query(DocumentTemplate).filter(
        DocumentTemplate.name == name
    ).first()
    if existing_template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template with this name already exists"
        )
    
    # Read file content
    content = await file.read()
    
    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Generate safe filename with UUID
    original_filename = file.filename or "template.pdf"
    safe_filename = f"{uuid.uuid4()}_{original_filename}"
    
    # Validate path safety - ensure file goes to correct directory
    templates_dir = os.path.join(settings.storage_dir, "templates")
    os.makedirs(templates_dir, exist_ok=True)
    file_path = os.path.join(templates_dir, safe_filename)
    
    # Verify path is within templates directory (prevent directory traversal)
    if not os.path.abspath(file_path).startswith(os.path.abspath(templates_dir)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path"
        )
    
    # Save file
    file_path = TemplateService.save_template_file(content, safe_filename)
    
    # Create template record
    template = DocumentTemplate(
        name=name,
        description=description,
        file_name=original_filename,  # Store original name for display
        file_path=file_path,
        mime_type=file.content_type,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    
    # Log action
    AuditService.log_action(
        db,
        admin_user.id,
        "TEMPLATE_UPLOADED",
        details=f"Uploaded template: {name}"
    )
    
    return template


@router.get("/", response_model=List[DocumentTemplateResponse])
async def list_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    """List all available document templates."""
    templates = db.query(DocumentTemplate).offset(skip).limit(limit).all()
    return templates


@router.get("/{template_id}", response_model=DocumentTemplateResponse)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific template."""
    template = db.query(DocumentTemplate).filter(DocumentTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Delete a document template (admin only)."""
    template = db.query(DocumentTemplate).filter(DocumentTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Delete file
    TemplateService.delete_template_file(template.file_path)
    
    # Delete record
    db.delete(template)
    db.commit()
    
    # Log action
    AuditService.log_action(
        db,
        admin_user.id,
        "TEMPLATE_DELETED",
        details=f"Deleted template: {template.name}"
    )
