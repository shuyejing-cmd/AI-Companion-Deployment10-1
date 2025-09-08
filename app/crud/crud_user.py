# app/crud/crud_user.py (最终异步版)

from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.future import select # 导入 select

from app.models.user import User
from app.schemas.user import UserCreate

# 关键改动 1：函数改为 async def，并适配新的查询语法
async def get_user_by_openid(db: Session, openid: str) -> User | None:
    """
    通过 openid 查询用户 (异步)
    """
    result = await db.execute(select(User).filter(User.openid == openid))
    return result.scalar_one_or_none()

# 关键改动 2：函数改为 async def，并 await IO操作
async def create_user(db: Session, user_in: UserCreate) -> User:
    """
    创建一个新用户 (异步)
    """
    db_user = User(**user_in.model_dump())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# 关键改动 3：函数改为 async def，并适配新的查询语法
async def get_user(db: Session, user_id: UUID) -> User | None:
    """
    通过 user_id 查询用户 (异步)
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()