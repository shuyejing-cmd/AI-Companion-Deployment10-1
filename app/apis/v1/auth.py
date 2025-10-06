# app/apis/v1/auth.py (最终异步版)

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # 1. 导入用于处理登录表单的类
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.schemas import user as user_schema
from app.crud import crud_user
from app.apis.dependencies import get_async_db
# 2. 导入我们刚刚创建的所有新工具函数
from app.core.security import create_jwt_for_user, verify_password, get_password_hash

router = APIRouter()

# class WechatLoginRequest(BaseModel): # <--- 删除旧的模型
#     code: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# --- ▼▼▼ 这里是修改的核心区域 ▼▼▼ ---

# 3. 删除或注释掉整个微信登录函数
# @router.post("/auth/wechat", ...)
# async def login_wechat(...):
#     ...

# --- 新增：用户注册接口 ---
@router.post("/auth/register", response_model=user_schema.User, status_code=status.HTTP_201_CREATED)
async def register_new_user(
    *,
    user_in: user_schema.UserCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    处理新用户通过邮箱和密码进行注册。
    """
    # 检查用户是否已存在
    existing_user = await crud_user.get_user_by_email(db=db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="该邮箱已被注册，请直接登录或使用其他邮箱。",
        )
    
    # 将明文密码哈希化
    hashed_password = get_password_hash(user_in.password)
    
    # 在数据库中创建用户
    user = await crud_user.create_user(
        db=db,
        email=user_in.email,
        hashed_password=hashed_password,
        nickname=user_in.nickname
    )
    return user

# --- 新增：用户登录接口 ---
@router.post("/auth/login", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
):
    """
    处理用户登录请求，验证成功后返回 access_token。
    FastAPI 的 OAuth2PasswordRequestForm 会自动解析 "username" 和 "password" 字段。
    """
    # 通过 email (在表单中是 username 字段) 查找用户
    user = await crud_user.get_user_by_email(db=db, email=form_data.username)
    
    # 验证用户是否存在以及密码是否正确
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"}, # 这是OAuth2标准的一部分
        )
    
    # 如果验证成功，为用户创建 JWT (这部分逻辑完全复用)
    access_token = create_jwt_for_user(user.id)
    return {"access_token": access_token, "token_type": "bearer"}

# --- ▲▲▲ 修改完成 ▲▲▲ ---