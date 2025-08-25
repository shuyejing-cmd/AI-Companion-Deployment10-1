from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

# 文件状态的基础模型
class KnowledgeFileBase(BaseModel):
    file_name: str

# 从 API 读取文件信息时的模型
class KnowledgeFileRead(KnowledgeFileBase):
    id: UUID
    status: str
    error_message: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

# 创建文件记录时内部使用的模型
class KnowledgeFileCreate(KnowledgeFileBase):
    file_path: str
    companion_id: UUID