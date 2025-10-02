import uuid
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # --- ▼▼▼ 这里是修改的核心区域 ▼▼▼ ---
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    # --- ▲▲▲ 修改完成 ▲▲▲ ---

    nickname = Column(String, index=True)
    avatar_url = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    companions = relationship(
        "Companion",
        cascade="all, delete-orphan",
        back_populates="owner",
        passive_deletes=True,
    )