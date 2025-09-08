# app/crud/crud_companion.py (最终异步版)

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.companion import Companion
from app.schemas.companion import CompanionCreate, CompanionUpdate

async def create_companion(db: AsyncSession, companion_in: CompanionCreate, user_id: UUID) -> Companion:
    """
    为指定用户创建一个新的 AI 伙伴 (异步)。
    """
    companion_data = companion_in.model_dump()
    db_companion = Companion(**companion_data, user_id=user_id)
    db.add(db_companion)
    await db.commit()
    await db.refresh(db_companion)
    return db_companion

async def get_companion_by_id(db: AsyncSession, companion_id: UUID) -> Optional[Companion]:
    """
    通过 ID 获取一个 AI 伙伴 (异步)。
    """
    result = await db.execute(select(Companion).filter(Companion.id == companion_id))
    return result.scalar_one_or_none()

async def get_multi_companions_by_owner(db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Companion]:
    """
    获取一个用户拥有的所有 AI 伙伴列表 (异步)。
    """
    result = await db.execute(
        select(Companion)
        .filter(Companion.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_companion(
    db: AsyncSession, db_companion: Companion, companion_in: CompanionUpdate
) -> Companion:
    """
    更新一个 AI 伙伴的信息 (异步)。
    """
    update_data = companion_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_companion, field, value)
        
    db.add(db_companion)
    await db.commit()
    await db.refresh(db_companion)
    return db_companion

async def delete_companion(db: AsyncSession, db_companion: Companion) -> Companion:
    """
    删除一个 AI 伙伴 (异步)。
    """
    await db.delete(db_companion)
    await db.commit()
    return db_companion