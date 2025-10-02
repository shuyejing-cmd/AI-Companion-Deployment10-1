# app/apis/dependencies.py (最终异步版)

from typing import Generator
from uuid import UUID

from fastapi import Depends, HTTPException, status, Query, WebSocket,Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session # 保留给同步的 get_db
import redis.asyncio as redis

from app.core.config import settings
from app.db.session import SessionLocal, AsyncSessionLocal # 导入异步会话
from app.models.user import User
from app.crud import crud_user

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login" # 将 'wechat' 修改为 'login'
)

# 这个 get_db 依赖现在主要给 Alembic 或其他同步脚本使用
# FastAPI 的异步端点将使用下面的 get_async_db
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db() -> Generator[AsyncSession, None, None]:
    """为异步API端点提供数据库会话。"""
    async with AsyncSessionLocal() as session:
        yield session

async def get_redis_client(request: Request) -> redis.Redis:
    """
    依赖项，从 app.state 中获取 Redis 客户端实例。
    """
    if not hasattr(request.app.state, 'redis_client'):
        raise RuntimeError("Redis client is not available in app.state. Check startup event.")
    return request.app.state.redis_client        

async def get_redis_client_ws(websocket: WebSocket) -> redis.Redis:
    """
    依赖项，为 WebSocket 提供在 app.state 中存储的 Redis 客户端实例。
    """
    if not hasattr(websocket.app.state, 'redis_client'):
        raise RuntimeError("Redis client is not available in app.state. Check startup event.")
    # 直接返回在启动时创建的那个共享的客户端实例
    return websocket.app.state.redis_client

async def get_current_user(
    db: AsyncSession = Depends(get_async_db), token: str = Depends(reusable_oauth2)
) -> User:
    """
    用于普通 REST API 的依赖项 (异步)。
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )
        user_id = UUID(user_id_str)
    except (JWTError, ValidationError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    user = await crud_user.get_user(db=db, user_id=user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def get_current_user_from_token(
    token: str = Query(...),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """
    专门为 WebSocket 创建的认证函数 (异步)。
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials: user_id is missing",
            )
        user_id = UUID(user_id_str)
    except (JWTError, ValidationError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    user = await crud_user.get_user(db=db, user_id=user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user