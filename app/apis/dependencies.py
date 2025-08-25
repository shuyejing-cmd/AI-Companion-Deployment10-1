from typing import Generator
from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from pydantic import ValidationError
import redis.asyncio as redis

from app.db.session import SessionLocal
from app.core.config import settings
from app.models.user import User

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/wechat")

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
# --- 新增结束 ---


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    from uuid import UUID
    user = db.query(User).filter(User.id == UUID(user_id)).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user