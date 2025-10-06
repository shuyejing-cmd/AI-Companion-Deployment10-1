# app/schemas/user.py

import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr, HttpUrl # 确保导入 HttpUrl
from datetime import datetime

# 基础模型，包含所有模型共有的字段
class UserBase(BaseModel):
    email: EmailStr
    nickname: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None # <-- 修正：统一为 HttpUrl

# 用于创建新用户的模型
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    nickname: Optional[str] = None

# 用于更新用户头像的模型
class UserAvatarUpdate(BaseModel):
    avatar_url: HttpUrl

# --- 最终版本 ---
# 用于从 API 读取/返回用户数据的统一模型
class User(UserBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True