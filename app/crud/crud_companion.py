from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.companion import Companion
from app.schemas.companion import CompanionCreate, CompanionUpdate

def create_companion(db: Session, companion_in: CompanionCreate, user_id: UUID) -> Companion:
    """
    为指定用户创建一个新的 AI 伙伴。
    """
    # 将 Pydantic 模型转换为字典，并添加 user_id
    companion_data = companion_in.model_dump()
    db_companion = Companion(**companion_data, user_id=user_id)
    db.add(db_companion)
    db.commit()
    db.refresh(db_companion)
    return db_companion

def get_companion_by_id(db: Session, companion_id: UUID) -> Optional[Companion]:
    """
    通过 ID 获取一个 AI 伙伴。
    """
    return db.query(Companion).filter(Companion.id == companion_id).first()

def get_multi_companions_by_owner(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Companion]:
    """
    获取一个用户拥有的所有 AI 伙伴列表。
    """
    return (
        db.query(Companion)
        .filter(Companion.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def update_companion(
    db: Session, db_companion: Companion, companion_in: CompanionUpdate
) -> Companion:
    """
    更新一个 AI 伙伴的信息。
    """
    # 将 Pydantic 模型转换为字典，只保留被设置了值的字段
    update_data = companion_in.model_dump(exclude_unset=True)
    
    # 遍历字典，更新数据库对象的属性
    for field, value in update_data.items():
        setattr(db_companion, field, value)
        
    db.add(db_companion)
    db.commit()
    db.refresh(db_companion)
    return db_companion

def delete_companion(db: Session, db_companion: Companion) -> Companion:
    """
    删除一个 AI 伙伴。
    """
    db.delete(db_companion)
    db.commit()
    return db_companion