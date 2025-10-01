import os
from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge_file import KnowledgeFile
from app.schemas import knowledge_file as kf_schema

async def create_knowledge_file(db: AsyncSession, *, file_in: kf_schema.KnowledgeFileCreate, file_id: UUID) -> KnowledgeFile:
    """
    (异步) 使用预先生成的 ID 在数据库中创建一个新的知识文件记录。
    """
    db_file = KnowledgeFile(
        id=file_id, # <-- 1. 直接使用传入的 file_id
        file_name=file_in.file_name,
        file_path=file_in.file_path,
        companion_id=file_in.companion_id
    )
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)
    return db_file

async def get_file_by_id(db: AsyncSession, *, file_id: UUID) -> Optional[KnowledgeFile]:
    query = select(KnowledgeFile).where(KnowledgeFile.id == file_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_files_by_companion(db: AsyncSession, *, companion_id: UUID) -> List[KnowledgeFile]:
    query = select(KnowledgeFile).where(KnowledgeFile.companion_id == companion_id).order_by(KnowledgeFile.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

async def remove_file(db: AsyncSession, *, file_to_delete: KnowledgeFile) -> None:
    if os.path.exists(file_to_delete.file_path):
        try:
            os.remove(file_to_delete.file_path)
        except OSError as e:
            print(f"Error deleting physical file {file_to_delete.file_path}: {e}")
    await db.delete(file_to_delete)
    await db.commit()

async def update_status(db: AsyncSession, *, file_id: UUID, status: str, error_message: str | None = None) -> KnowledgeFile | None:
    db_file = await get_file_by_id(db, file_id=file_id)
    if db_file:
        db_file.status = status
        if error_message is not None:
            db_file.error_message = error_message
        await db.commit()
        await db.refresh(db_file)
    return db_file