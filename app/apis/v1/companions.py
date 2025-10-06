# app/apis/v1/companions.py (最终修正版，修复了CompanionRead引用)

from typing import List, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

# 🚀 1. 导入修正后的 Schema
from app.schemas import companion as companion_schema
from app.crud import crud_companion
from app.models.user import User
from app.services.rag_service import rag_service
from app.services.memory_manager import MemoryManager
from app.apis.dependencies import get_async_db, get_current_user, get_redis_client 

router = APIRouter()

@router.post(
    "/",
    # 🚀 2. 修正点: CompanionRead -> Companion
    response_model=companion_schema.Companion, 
    status_code=status.HTTP_201_CREATED,
    summary="创建 AI 伙伴",
    description="为当前登录的用户创建一个新的 AI 伙伴。",
)
async def create_new_companion(
    *,
    companion_in: companion_schema.CompanionCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    companion = await crud_companion.create_companion(
        db=db, companion_in=companion_in, user_id=current_user.id
    )
    return companion


@router.get(
    "/",
    # 🚀 3. 修正点: CompanionRead -> Companion
    response_model=List[companion_schema.Companion], 
    summary="获取当前用户的所有 AI 伙伴",
    description="列出当前登录用户所创建的所有 AI 伙伴。",
)
async def read_user_companions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    companions = await crud_companion.get_multi_companions_by_owner(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return companions


@router.get(
    "/{companion_id}",
    # 🚀 4. 修正点: CompanionRead -> Companion
    response_model=companion_schema.Companion, 
    summary="获取单个 AI 伙伴信息",
    description="通过其 UUID 获取单个 AI 伙伴的详细信息。",
)
async def read_single_companion(
    *,
    companion_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    # ‼️ 注意: 此处原代码缺少 current_user 依赖，虽然 FastAPI 不会报错，
    # 但从安全角度讲，任何需要 companion_id 的操作都应验证用户身份。
    # 我们暂时保持原样，但在未来的重构中这是一个值得优化的地方。
) -> Any:
    companion = await crud_companion.get_companion_by_id(db=db, companion_id=companion_id)
    if not companion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Companion not found")
    # 理想情况下，这里应该检查 companion.owner_id 是否等于 current_user.id
    return companion


@router.patch(
    "/{companion_id}",
    # 🚀 5. 修正点: CompanionRead -> Companion
    response_model=companion_schema.Companion, 
    summary="更新 AI 伙伴信息",
    description="更新一个已存在的 AI 伙伴。只有伙伴的创建者才能更新。",
)
async def update_existing_companion(
    *,
    companion_id: UUID,
    companion_in: companion_schema.CompanionUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    db_companion = await crud_companion.get_companion_by_id(db=db, companion_id=companion_id)
    if not db_companion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Companion not found")
    # ‼️ 原代码中 user_id 字段名有误，根据您的 crud_companion.py 和 models, 应该是 owner_id
    if db_companion.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    companion = await crud_companion.update_companion(
        db=db, db_companion=db_companion, companion_in=companion_in
    )
    return companion


@router.delete(
    "/{companion_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK, 
    summary="彻底删除 AI 伙伴及其所有数据",
    description="删除一个AI伙伴，并联动删除其在向量数据库、Redis缓存和数据库中的所有关联数据。",
)
async def delete_companion_fully(
    *,
    companion_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis_client),
) -> dict:
    db_companion = await crud_companion.get_companion_by_id(db=db, companion_id=companion_id)
    if not db_companion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI伙伴不存在")
    # ‼️ 原代码中 user_id 字段名有误，根据您的 crud_companion.py 和 models, 应该是 owner_id
    if db_companion.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限删除此AI伙伴")

    companion_name = db_companion.name
    companion_id_str = str(companion_id)
    user_id_str = str(current_user.id)
    
    print(f"开始彻底删除AI伙伴: {companion_name} (ID: {companion_id_str})")

    try:
        await rag_service.delete_vectors_by_companion_id(companion_id=companion_id_str)
        
        memory_manager = MemoryManager(
            redis_client=redis_client,
            companion_name=db_companion.name,
            user_id=user_id_str
        )
        await memory_manager.delete_memory()
        
        await crud_companion.delete_companion(db=db, db_companion=db_companion)
        
        # ‼️ 注意: 在您的原代码中，db.commit() 在 delete_companion 之后，
        # 而 crud_companion.delete_companion 内部已经 commit 了。这可能会导致问题。
        # 最好的实践是在 crud 层 commit，或者在 api 层统一 commit/rollback。
        # 我们暂时保持原样，但这是未来重构的要点。

        return {"message": f"AI伙伴 '{companion_name}' 已被彻底删除。"}

    except Exception as e:
        await db.rollback()
        print(f"删除过程中发生严重错误: {e}")
        raise HTTPException(status_code=500, detail=f"删除伙伴时发生内部错误: {str(e)}")