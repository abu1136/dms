from datetime import datetime
from pydantic import BaseModel, Field


class UserBasic(BaseModel):
    id: int
    username: str
    email: str
    
    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    title: str
    template_id: int | None = None


class DocumentCreate(DocumentBase):
    content: str = ""


class DocumentResponse(DocumentBase):
    id: int
    document_number: str
    requested_by_id: int
    created_at: datetime
    file_name: str
    requested_by: UserBasic | None = None

    class Config:
        from_attributes = True


class DocumentFilter(BaseModel):
    document_number: str | None = None
    title: str | None = None
    user_id: int | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
