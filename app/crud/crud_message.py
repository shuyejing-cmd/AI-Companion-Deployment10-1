from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.message import Message
from app.schemas.message import MessageCreate

def create_message(
    db: Session, message_in: MessageCreate, user_id: UUID
) -> Message:
    """
    创建一条新的聊天记录。
    """
    db_message = Message(
        content=message_in.content,
        role=message_in.role,
        companion_id=message_in.companion_id,
        user_id=user_id,
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_messages_by_companion(
    db: Session, companion_id: UUID, user_id: UUID, skip: int = 0, limit: int = 20
) -> List[Message]:
    """
    获取指定 AI 伙伴与用户的聊天记录（按时间倒序）。
    """
    return (
        db.query(Message)
        .filter(Message.companion_id == companion_id, Message.user_id == user_id)
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )