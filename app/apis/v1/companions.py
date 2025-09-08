# app/apis/v1/companions.py (最终完美异步版)

from typing import List, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import companion as companion_schema
from app.crud import crud_companion
from app.models.user import User
from app.apis.dependencies import get_async_db, get_current_user

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
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除 AI 伙伴",
    description="删除一个已存在的 AI 伙伴。只有伙伴的创建者才能删除。",
)
async def delete_existing_companion(
    *,
    companion_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    db_companion = await crud_companion.get_companion_by_id(db=db, companion_id=companion_id)
    if not db_companion:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    if db_companion.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    await crud_companion.delete_companion(db=db, db_companion=db_companion)
    return Response(status_code=status.HTTP_204_NO_CONTENT)