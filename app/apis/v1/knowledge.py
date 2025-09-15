from uuid import UUID, uuid4
from pathlib import Path
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from arq.connections import ArqRedis

from app.schemas import knowledge_file as kf_schema
from app.crud import crud_knowledge_file, crud_companion
from app.models.user import User
from app.apis.dependencies import get_async_db, get_current_user

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post(
    "/companions/{companion_id}/knowledge",
    response_model=kf_schema.KnowledgeFileRead,
    status_code=status.HTTP_202_ACCEPTED,
    summary="上传知识文件"
)
async def upload_knowledge_file(
    *,
    request: Request,
    companion_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
):
    companion = await crud_companion.get_companion_by_id(db=db, companion_id=companion_id)
    if not companion or companion.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Companion not found or access denied")

    try:
        db_file_id = uuid4()
        file_dir = UPLOAD_DIR / str(companion_id) / str(db_file_id)
        file_dir.mkdir(parents=True, exist_ok=True)
        file_path = file_dir / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        await file.close()

    file_in = kf_schema.KnowledgeFileCreate(
        file_name=file.filename,
        file_path=str(file_path),
        companion_id=companion_id,
    )

    # 确保这一行是完整且正确的
    db_file = await crud_knowledge_file.create_knowledge_file(
        db=db, file_in=file_in, file_id=db_file_id
    )

    arq_pool: ArqRedis = request.app.state.arq_pool
    await arq_pool.enqueue_job("process_file_task", db_file.id)
    return db_file


@router.get(
    "/companions/{companion_id}/knowledge",
    response_model=List[kf_schema.KnowledgeFileRead],
    summary="获取伙伴的知识文件列表"
)
async def get_knowledge_files_for_companion(
    *,
    companion_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    companion = await crud_companion.get_companion_by_id(db=db, companion_id=companion_id)
    if not companion or companion.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Companion not found or access denied")
    files = await crud_knowledge_file.get_files_by_companion(db=db, companion_id=companion_id)
    return files


@router.delete(
    "/knowledge/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除知识文件"
)
async def delete_knowledge_file(
    *,
    request: Request,
    file_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    file_to_delete = await crud_knowledge_file.get_file_by_id(db=db, file_id=file_id)
    if not file_to_delete:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    companion = await crud_companion.get_companion_by_id(db=db, companion_id=file_to_delete.companion_id)
    if not companion or companion.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this file")
    await crud_knowledge_file.remove_file(db=db, file_to_delete=file_to_delete)
    arq_pool: ArqRedis = request.app.state.arq_pool
    await arq_pool.enqueue_job("cleanup_pinecone_task", str(file_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)