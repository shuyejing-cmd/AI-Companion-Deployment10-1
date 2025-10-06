# app/models/user.py

import uuid
from sqlalchemy import Column, String, DateTime, func, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, INTEGER
from app.db.base_class import Base
from sqlalchemy.orm import relationship, Mapped, mapped_column # 导入 Mapped 和 mapped_column
from typing import TYPE_CHECKING, List, Optional
from datetime import datetime
from app.db.base_class import Base

# 检查依赖，避免循环导入
if TYPE_CHECKING:
    from .companion import Companion # noqa: F401

class User(Base):
    __tablename__ = "users"

    # 使用 SQLAlchemy 2.0 Mapped 风格
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    # 修正：采用 Mapped 风格，并设置长度限制
    nickname: Mapped[Optional[str]] = mapped_column(String(256), index=True, nullable=True)
    
    #  NEW: 用户头像URL，修正后版本，保持一致的 512 长度
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="用户头像URL，存储在COS上")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # relationships
    companions: Mapped[List["Companion"]] = relationship(
        "Companion",
        cascade="all, delete-orphan",
        back_populates="owner",
        passive_deletes=True,
    )