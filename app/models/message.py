import uuid
from sqlalchemy import Column, Text, ForeignKey, func, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 消息内容
    content = Column(Text, nullable=False)
    
    # 消息角色：'user' 或 'ai'
    role = Column(String(10), nullable=False)
    
    
    # 外键，关联到 companions 表
    companion_id = Column(UUID(as_uuid=True), ForeignKey("companions.id", ondelete="CASCADE"), nullable=False, index=True)
    # 外键，关联到 users 表
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    created_at = Column(DateTime, server_default=func.now())
    
    # 建立关系 (可选，但推荐)
    companion = relationship("Companion")
    user = relationship("User")