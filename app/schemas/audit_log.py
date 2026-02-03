from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UserBasic(BaseModel):
    id: int
    username: str
    email: str
    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    document_id: int | None
    timestamp: datetime
    details: str | None
    user: UserBasic | None = None

    model_config = ConfigDict(from_attributes=True)
