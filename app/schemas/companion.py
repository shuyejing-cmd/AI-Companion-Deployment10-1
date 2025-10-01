from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

# 共有的基础字段
class CompanionBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    instructions: str
    seed: str
    src: Optional[str] = None
    category_id: Optional[str] = None

# 创建时需要接收的字段
class CompanionCreate(CompanionBase):
    pass

# 更新时可以只接收部分字段，所有字段都变为可选
class CompanionUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    instructions: Optional[str] = None
    seed: Optional[str] = None
    src: Optional[str] = None
    category_id: Optional[str] = None

# 从 API 读取/返回时的字段
class CompanionRead(CompanionBase):
    id: UUID
    user_id: UUID

    class Config:
        from_attributes = True