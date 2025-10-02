from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

# --- ▼▼▼ 这里是修改的核心区域 ▼▼▼ ---

# 基础模型，包含所有模型共有的字段
class UserBase(BaseModel):
    email: EmailStr  # 使用 EmailStr 自动验证邮箱格式
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None

# 用于创建新用户的模型
# 不再继承 UserBase，因为它需要接收明文密码
class UserCreate(BaseModel):
    email: EmailStr
    password: str # 注册时API会接收这个明文密码
    nickname: Optional[str] = None

# 用于从 API 读取/返回用户数据的模型
class UserRead(UserBase):
    id: UUID
    created_at: datetime

    # Pydantic V2 的配置方式，告诉 Pydantic 模型可以从 ORM 对象（数据库模型）中读取数据
    class Config:
        from_attributes = True

# --- ▲▲▲ 修改完成 ▲▲▲ ---