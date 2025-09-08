# app/apis/v1/companions.py (最终异步版)

from typing import List, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import companion as companion_schema
from app.crud import crud_companion
from app.models.user import User
# 关键修改：导入 get_async_db
from app.apis.dependencies import get_async_db, get_current_user

router = APIRouter()

@router.post("/", ...)
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

@router.get("/", ...)
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

@router.get("/{companion_id}", ...)
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

@router.patch("/{companion_id}", ...)
async def update_existing_companion(
    *,
    companion_id: UUID,
    companion_in: companion_schema.CompanionUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    # 注意：这里需要分两步 await
    db_companion = await crud_companion.get_companion_by_id(db=db, companion_id=companion_id)
    if not db_companion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Companion not found")
    if db_companion.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    companion = await crud_companion.update_companion(
        db=db, db_companion=db_companion, companion_in=companion_in
    )
    return companion

@router.delete("/{companion_id}", ...)
async def delete_existing_companion(
    *,
    companion_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    # 注意：这里需要分两步 await
    db_companion = await crud_companion.get_companion_by_id(db=db, companion_id=companion_id)
    if not db_companion:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    if db_companion.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    await crud_companion.delete_companion(db=db, db_companion=db_companion)
    return Response(status_code=status.HTTP_204_NO_CONTENT)