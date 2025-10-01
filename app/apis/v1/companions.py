# app/apis/v1/companions.py (最终完美异步版)

from typing import List, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.schemas import companion as companion_schema
from app.crud import crud_companion
from app.models.user import User
from app.services.rag_service import rag_service # 引入 RAG 服务单例
from app.services.memory_manager import MemoryManager
from app.apis.dependencies import get_async_db, get_current_user, get_redis_client 


router = APIRouter()

@router.post(
    "/",
    response_model=companion_schema.CompanionRead,
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
    response_model=List[companion_schema.CompanionRead],
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
    response_model=companion_schema.CompanionRead,
    summary="获取单个 AI 伙伴信息",
    description="通过其 UUID 获取单个 AI 伙伴的详细信息。",
)
async def read_single_companion(
    *,
    companion_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    companion = await crud_companion.get_companion_by_id(db=db, companion_id=companion_id)
    if not companion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Companion not found")
    return companion


@router.patch(
    "/{companion_id}",
    response_model=companion_schema.CompanionRead,
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
    if db_companion.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    companion = await crud_companion.update_companion(
        db=db, db_companion=db_companion, companion_in=companion_in
    )
    return companion


@router.delete(
    "/{companion_id}",
    # --- ↓↓↓ 修改点1: 修改返回模型和状态码，提供更清晰的反馈 ↓↓↓ ---
    response_model=dict,
    status_code=status.HTTP_200_OK, 
    summary="彻底删除 AI 伙伴及其所有数据",
    description="删除一个AI伙伴，并联动删除其在向量数据库、Redis缓存和数据库中的所有关联数据。",
)
async def delete_companion_fully( # <-- 函数名修改以反映其功能
    *,
    companion_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis_client),
) -> dict:
    # 1. 获取伙伴信息，并严格验证所有权
    db_companion = await crud_companion.get_companion_by_id(db=db, companion_id=companion_id)
    if not db_companion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI伙伴不存在")
    if db_companion.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限删除此AI伙伴")

    companion_name = db_companion.name
    companion_id_str = str(companion_id)
    user_id_str = str(current_user.id)
    
    print(f"开始彻底删除AI伙伴: {companion_name} (ID: {companion_id_str})")

    try:
        # 2. 从向量数据库 (Pinecone) 删除
        await rag_service.delete_vectors_by_companion_id(companion_id=companion_id_str)

        # 3. 从 Redis 删除短期记忆
        # 关键：根据你的 MemoryManager 实现，我们需要使用 companion_name
        memory_manager = MemoryManager(
            redis_client=redis_client,
            companion_name=db_companion.name, # <-- 使用从数据库获取的 name
            user_id=user_id_str
        )
        await memory_manager.delete_memory()

        # 4. 从 PostgreSQL 删除伙伴主记录
        # (由于我们在模型中设置了 CASCADE，所有关联的 messages 会被数据库自动删除)
        print(f"  -> [API] 准备从 PostgreSQL 删除伙伴主记录...")
        await crud_companion.delete_companion(db=db, db_companion=db_companion)
        print(f"  -> [API] PostgreSQL 删除指令已发送。")

        # 5. 提交数据库事务
        await db.commit()
        print(f"删除操作成功完成，已提交数据库事务。")

        # 返回明确的成功信息
        return {"message": f"AI伙伴 '{companion_name}' 已被彻底删除。"}

    except Exception as e:
        # 如果任何一步失败，回滚数据库操作，确保数据一致性
        await db.rollback()
        print(f"删除过程中发生严重错误: {e}")
        # 抛出 500 错误，让前端知道操作失败了
        raise HTTPException(status_code=500, detail=f"删除伙伴时发生内部错误: {str(e)}")