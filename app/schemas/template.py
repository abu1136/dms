from datetime import datetime
from pydantic import BaseModel, Field


class DocumentTemplateBase(BaseModel):
    name: str
    description: str | None = None


class DocumentTemplateResponse(DocumentTemplateBase):
    id: int
    file_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    email: str | None = None
    is_active: bool | None = None
    role: str | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
