# app/apis/v1/users.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.schemas.user import User, UserAvatarUpdate
from app.crud import crud_user
from app.apis.dependencies import get_async_db, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.patch(
    "/me/avatar", 
    response_model=User,
    summary="更新当前用户的头像"
)
async def update_current_user_avatar(
    *,
    db: AsyncSession = Depends(get_async_db),
    avatar_in: UserAvatarUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    更新当前登录用户的头像URL。
    """
    try:
        # 🚀 调用我们新的、专属的CRUD函数
        updated_user = await crud_user.update_user_avatar(
            db=db,
            user=current_user,
            avatar_url=str(avatar_in.avatar_url) # Pydantic HttpUrl -> str
        )
        return updated_user
    except Exception as e:
        logger.error(f"Failed to update avatar for user {current_user.email}: {e}")
        raise HTTPException(status_code=500, detail="Could not update user avatar.")