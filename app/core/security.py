from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
from jose import JWTError, jwt
from app.core.config import settings

# --- ▼▼▼ 这里是新增的核心区域 ▼▼▼ ---
from passlib.context import CryptContext

# 创建一个密码上下文实例，指定使用 bcrypt 哈希算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码是否与哈希后的密码匹配。
    
    :param plain_password: 用户登录时提交的原始密码。
    :param hashed_password: 数据库中存储的哈希密码。
    :return: 如果匹配则返回 True，否则返回 False。
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    为给定的明文密码生成哈希值。
    
    :param password: 用户注册时提交的原始密码。
    :return: 加密后的密码哈希字符串。
    """
    return pwd_context.hash(password)
# --- ▲▲▲ 新增完成 ▲▲▲ ---


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT access token - 此函数无需修改
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_jwt_for_user(user_id: UUID) -> str:
    """
    为指定用户创建一个 JWT access token - 此函数无需修改
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_access_token(
        data={"sub": str(user_id)}, expires_delta=access_token_expires
    )