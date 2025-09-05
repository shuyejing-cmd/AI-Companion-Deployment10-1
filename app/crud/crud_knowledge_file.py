# app/crud/crud_knowledge_file.py

from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge_file import KnowledgeFile
from app.schemas import knowledge_file as kf_schema

# --- 同步函数 (用于 API) ---
def create_knowledge_file(db: Session, *, file_in: kf_schema.KnowledgeFileCreate) -> KnowledgeFile:
    """
    在数据库中创建一个新的知识文件记录。
    """
    db_file = KnowledgeFile(
        file_name=file_in.file_name,
        file_path=file_in.file_path,
        companion_id=file_in.companion_id,
        # 初始状态由模型默认设置
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

# --- ↓↓↓ 新增的、至关重要的异步函数 (用于 Worker) ↓↓↓ ---
async def update_status(
    db: AsyncSession, *, file_id: UUID, status: str, error_message: str | None = None
) -> KnowledgeFile | None:
    """
    (异步) 更新指定知识文件的状态和错误信息。
    """
    query = select(KnowledgeFile).where(KnowledgeFile.id == file_id)
    result = await db.execute(query)
    db_file = result.scalar_one_or_none()
    
    if db_file:
        db_file.status = status
        # 只有在提供了 error_message 时才更新它
        if error_message is not None:
            db_file.error_message = error_message
            
        await db.commit()
        await db.refresh(db_file)
        
    return db_file