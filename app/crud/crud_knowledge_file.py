from uuid import UUID
from sqlalchemy.orm import Session

from app.models.knowledge_file import KnowledgeFile
from app.schemas.knowledge_file import KnowledgeFileCreate

def create_knowledge_file(db: Session, *, file_in: KnowledgeFileCreate) -> KnowledgeFile:
    """
    在数据库中创建一条新的知识文件记录。
    """
    db_file = KnowledgeFile(
        file_name=file_in.file_name,
        file_path=file_in.file_path,
        companion_id=file_in.companion_id
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_knowledge_file_by_id(db: Session, *, file_id: UUID) -> KnowledgeFile | None:
    """
    通过 ID 获取一个知识文件记录。
    """
    return db.query(KnowledgeFile).filter(KnowledgeFile.id == file_id).first()

# 我们未来还会在这里添加 update, delete 等函数