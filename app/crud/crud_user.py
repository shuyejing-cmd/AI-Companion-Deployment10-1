# app/crud/crud_user.py (最终异步版)

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
# 注意：我们不再需要从 schemas 导入 UserCreate，因为创建逻辑已改变
# from app.schemas.user import UserCreate 

# --- ▼▼▼ 这里是修改的核心区域 ▼▼▼ ---

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """
    通过 email 查询用户 (异步)
    """
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, *, email: str, hashed_password: str, nickname: str | None = None) -> User:
    """
    创建一个新用户 (异步)
    """
    db_user = User(
        email=email,
        hashed_password=hashed_password,
        nickname=nickname
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# --- ▲▲▲ 修改完成 ▲▲▲ ---

async def get_user(db: AsyncSession, user_id: UUID) -> User | None:
    """
    通过 user_id 查询用户 (异步) - 此函数保持不变
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()