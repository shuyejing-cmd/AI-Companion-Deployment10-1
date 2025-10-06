# app/models/companion.py

import uuid
from sqlalchemy import Column, String, Text, ForeignKey, func, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column # 导入 Mapped 和 mapped_column
from typing import TYPE_CHECKING, Optional, List
from datetime import datetime
from app.db.base_class import Base

if TYPE_CHECKING:
    from .user import User # noqa: F401
    from .knowledge_file import KnowledgeFile # noqa: F401

class Companion(Base):
    __tablename__ = "companions"

    # 使用 SQLAlchemy 2.0 Mapped 风格
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 外键，关联到 users 表的 id 字段，并使用 Mapped 风格和 CASCADE 删除
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False) # 'instructions' 相当于角色的核心 Prompt
    seed: Mapped[str] = mapped_column(Text, nullable=False) # 'seed' 相当于示例对话或角色的口头禅
    
    # 🚀 NEW: AI 伙伴头像URL，替换了原有的 'src' 字段
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="AI伙伴头像URL，存储在COS上")
    
    # 假设有一个类别 ID
    category_id: Mapped[Optional[str]] = mapped_column(String, nullable=True) 

    pinecone_index_name: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True, index=True)
    knowledge_base_status: Mapped[str] = mapped_column(String(20), default='EMPTY', nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # relationships
    owner: Mapped["User"] = relationship("User", back_populates="companions")
    knowledge_files: Mapped[List["KnowledgeFile"]] = relationship(
        "KnowledgeFile",
        cascade="all, delete-orphan",
        back_populates="companion",
        passive_deletes=True,
    )