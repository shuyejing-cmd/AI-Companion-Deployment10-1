from typing import List, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.schemas import companion as companion_schema
from app.crud import crud_companion
from app.models.user import User
from app.apis.dependencies import get_db, get_current_user

router = APIRouter()

@router.post(
    "/",
    response_model=companion_schema.CompanionRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建 AI 伙伴",
    description="为当前登录的用户创建一个新的 AI 伙伴。",
)
def create_new_companion(
    *,
    companion_in: companion_schema.CompanionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    创建一个 AI 伙伴。

    - **name**: 伙伴的名称 (必填)
    - **description**: 伙伴的简短描述 (必填)
    - **instructions**: 对伙伴的核心人设和行为指令 (必填)
    - **seed**: 伙伴的示例对话或口头禅 (必填)
    """
    companion = crud_companion.create_companion(
        db=db, companion_in=companion_in, user_id=current_user.id
    )
    return companion


@router.get(
    "/",
    response_model=List[companion_schema.CompanionRead],
    summary="获取当前用户的所有 AI 伙伴",
    description="列出当前登录用户所创建的所有 AI 伙伴。",
)
def read_user_companions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取当前用户的所有 AI 伙伴列表。
    """
    companions = crud_companion.get_multi_companions_by_owner(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return companions


@router.get(
    "/{companion_id}",
    response_model=companion_schema.CompanionRead,
    summary="获取单个 AI 伙伴信息",
    description="通过其 UUID 获取单个 AI 伙伴的详细信息。",
)
def read_single_companion(
    *,
    companion_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user), # 即使是读取，也需要验证用户以备将来扩展权限
) -> Any:
    """
    获取指定 ID 的 AI 伙伴信息。
    """
    companion = crud_companion.get_companion_by_id(db=db, companion_id=companion_id)
    if not companion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Companion not found")
    # 虽然目前任何登录用户都可以看，但加上这个权限判断是好的实践
    # 如果未来要做成私有伙伴，只需取消注释
    # if companion.user_id != current_user.id:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return companion


@router.patch(
    "/{companion_id}",
    response_model=companion_schema.CompanionRead,
    summary="更新 AI 伙伴信息",
    description="更新一个已存在的 AI 伙伴。只有伙伴的创建者才能更新。",
)
def update_existing_companion(
    *,
    companion_id: UUID,
    companion_in: companion_schema.CompanionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    更新一个 AI 伙伴。

    请求体中只需要包含你想更新的字段。
    """
    db_companion = crud_companion.get_companion_by_id(db=db, companion_id=companion_id)
    if not db_companion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Companion not found")
    if db_companion.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    companion = crud_companion.update_companion(
        db=db, db_companion=db_companion, companion_in=companion_in
    )
    return companion


@router.delete(
    "/{companion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除 AI 伙伴",
    description="删除一个已存在的 AI 伙伴。只有伙伴的创建者才能删除。",
)
def delete_existing_companion(
    *,
    companion_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    删除一个 AI 伙伴。

    成功删除后，将返回 `204 No Content` 状态码，响应体为空。
    """
    db_companion = crud_companion.get_companion_by_id(db=db, companion_id=companion_id)
    if not db_companion:
        # 即使找不到也返回 204，因为客户端的目标（确保它不存在）已经达成
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    if db_companion.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    crud_companion.delete_companion(db=db, db_companion=db_companion)
    return Response(status_code=status.HTTP_204_NO_CONTENT)