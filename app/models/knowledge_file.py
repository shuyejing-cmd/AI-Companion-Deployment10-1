import uuid
from sqlalchemy import Column, String, Text, ForeignKey, func, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base

# 定义一个文件状态的枚举类型，更规范
# 如果你的 PostgreSQL 版本支持，也可以使用 ENUM 类型
# from sqlalchemy import Enum
# class FileStatus(str, enum.Enum):
#     UPLOADED = "UPLOADED"
#     PROCESSING = "PROCESSING"
#     INDEXED = "INDEXED"
#     FAILED = "FAILED"

class KnowledgeFile(Base):
    __tablename__ = "knowledge_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    file_name = Column(String(255), nullable=False)
    # 存储文件在服务器上的相对路径
    file_path = Column(String(1024), nullable=False) 
    
    # 关联到 companions 表
    companion_id = Column(UUID(as_uuid=True), ForeignKey("companions.id"), nullable=False, index=True)
    
    # 文件处理状态，使用字符串
    status = Column(String(20), default='UPLOADED', nullable=False)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 建立与 Companion 模型的关系
    companion = relationship("Companion", back_populates="knowledge_files")