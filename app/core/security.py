# app/core/security.py

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
from jose import JWTError, jwt
from app.core.config import settings

# 核心修正：使用 passlib 的 CryptContext
from passlib.context import CryptContext

# 使用 bcrypt_sha256 方案，它会先对密码进行SHA-256哈希，
# 然后再用bcrypt处理结果，从而完美规避原生bcrypt的72字节长度限制。
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码是否与哈希后的密码匹配。
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    为给定的明文密码生成哈希值。
    """
    return pwd_context.hash(password)



def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_jwt_for_user(user_id: UUID) -> str:
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_access_token(
        data={"sub": str(user_id)}, expires_delta=access_token_expires
    )