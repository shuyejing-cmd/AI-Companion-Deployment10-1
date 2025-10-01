import uuid
from sqlalchemy import Column, String, Text, ForeignKey, func, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class Companion(Base):
    __tablename__ = "companions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 外键，关联到 users 表的 id 字段
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=False)
    instructions = Column(Text, nullable=False) # 'instructions' 相当于角色的核心 Prompt
    seed = Column(Text, nullable=False) # 'seed' 相当于示例对话或角色的口头禅
    
    # 假设我们有一个存放角色图片的 URL
    src = Column(String(1024))
    
    # 假设有一个类别 ID
    category_id = Column(String) # 这里我们先用 String，未来可以做成外键关联到 categories 表

    pinecone_index_name = Column(String, unique=True, nullable=True, index=True)
    knowledge_base_status = Column(String(20), default='EMPTY', nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 建立与 User 模型的关系
    # back_populates="companions" 告诉 SQLAlchemy 这个关系与 User 模型中的 'companions' 属性是对应的
    owner = relationship("User", back_populates="companions")

    knowledge_files = relationship("KnowledgeFile", cascade="all, delete-orphan", back_populates="companion")