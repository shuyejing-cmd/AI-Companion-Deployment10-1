# app/schemas/companion.py

import uuid
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl # 确保导入 HttpUrl

# 共有的基础字段
class CompanionBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    instructions: str
    seed: str
    avatar_url: Optional[HttpUrl] = None # <-- 核心修正：替换 src 并使用 HttpUrl
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
    avatar_url: Optional[HttpUrl] = None # <-- 核心修正：替换 src 并使用 HttpUrl
    category_id: Optional[str] = None

# 从 API 读取/返回时的字段
class Companion(CompanionBase): # <-- 统一命名为 Companion
    id: uuid.UUID
    owner_id: uuid.UUID # <-- 修正：根据您的 model，外键应为 owner_id

    class Config:
        from_attributes = True