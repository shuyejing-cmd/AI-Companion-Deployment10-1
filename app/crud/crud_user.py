# app/crud/crud_user.py (最终异步版)

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.schemas.user import UserCreate

async def get_user_by_openid(db: AsyncSession, openid: str) -> User | None:
    """
    通过 openid 查询用户 (异步)
    """
    result = await db.execute(select(User).filter(User.openid == openid))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """
    创建一个新用户 (异步)
    """
    db_user = User(**user_in.model_dump())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_user(db: AsyncSession, user_id: UUID) -> User | None:
    """
    通过 user_id 查询用户 (异步)
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()