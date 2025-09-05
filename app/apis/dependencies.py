# app/apis/dependencies.py (最终完整版)

from typing import Generator
from uuid import UUID

from fastapi import Depends, HTTPException, status, Query, WebSocket
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session
import redis.asyncio as redis

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User
from app.crud import crud_user

# --- ↓↓↓ 为普通 HTTP REST API 创建 OAuth2 scheme ↓↓↓ ---
# 它会告诉 FastAPI 去请求头 "Authorization: Bearer <token>" 中寻找 token
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/wechat"
)
# --- ↑↑↑ 添加结束 ↑↑↑ ---

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_redis_client_ws(websocket: WebSocket) -> redis.Redis:
    pool = websocket.app.state.redis_pool
    if pool is None:
        raise RuntimeError("Redis connection pool is not available in app.state.")
    return redis.Redis.from_pool(pool)


# --- ↓↓↓ 添加这个标准的 get_current_user 函数 ↓↓↓ ---
def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> User:
    """
    用于普通 REST API 的依赖项，从 Authorization header 解析 token 并获取用户。
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
    
    user = crud_user.get_user(db=db, user_id=user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
# --- ↑↑↑ 添加结束 ↑↑↑ ---


def get_current_user_from_token(
    token: str = Query(...),
    db: Session = Depends(get_db)
) -> User:
    """
    专门为 WebSocket 创建的认证函数，从 URL query 参数中解析 Token 并获取用户。
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
    
    user = crud_user.get_user(db=db, user_id=user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user