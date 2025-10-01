from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class MessageBase(BaseModel):
    content: str
    role: str = Field(..., pattern="^(user|ai)$") # 限制 role 只能是 'user' 或 'ai'

class MessageCreate(MessageBase):
    companion_id: UUID

class MessageRead(MessageBase):
    id: UUID
    companion_id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True