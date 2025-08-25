from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

# 基础模型，包含所有模型共有的字段
class UserBase(BaseModel):
    openid: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None

# 用于创建新用户的模型
# 在这个场景下，openid 是必须的
class UserCreate(UserBase):
    openid: str

# 用于从 API 读取/返回用户数据的模型
# 这将是我们 API 响应的格式
class UserRead(UserBase):
    id: UUID
    created_at: datetime

    # Pydantic V2 的配置方式，告诉 Pydantic 模型可以从 ORM 对象（数据库模型）中读取数据
    class Config:
        from_attributes = True