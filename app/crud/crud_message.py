from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.message import Message
from app.schemas.message import MessageCreate

async def create_message(
    db: AsyncSession, message_in: MessageCreate, user_id: UUID
) -> Message:
    """
    (异步) 创建一条新的聊天记录。
    """
    db_message = Message(
        content=message_in.content,
        role=message_in.role,
        companion_id=message_in.companion_id,
        user_id=user_id,
    )
    db.add(db_message)
    # 【【【关键修正：添加 await】】】
    await db.commit()
    await db.refresh(db_message)
    return db_message

async def get_messages_by_companion(
    db: AsyncSession, companion_id: UUID, user_id: UUID, skip: int = 0, limit: int = 20
) -> List[Message]:
    """
    (异步) 获取指定 AI 伙伴与用户的聊天记录（按时间倒序）。
    """
    # 【【【额外修正：改为异步查询语法】】】
    query = (
        select(Message)
        .where(Message.companion_id == companion_id, Message.user_id == user_id)
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


async def get_messages_by_companion_ascending(
    db: AsyncSession, *, companion_id: UUID, user_id: UUID, skip: int = 0, limit: int = 100
) -> List[Message]:
    """
    (异步) 获取指定AI伙伴与用户的聊天记录 (按时间正序)。
    """
    query = (
        select(Message)
        .where(Message.companion_id == companion_id, Message.user_id == user_id)
        .order_by(Message.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()