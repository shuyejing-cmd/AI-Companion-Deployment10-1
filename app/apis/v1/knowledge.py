# app/apis/v1/knowledge.py (最终修正版)

from uuid import UUID, uuid4
from pathlib import Path
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from arq.connections import ArqRedis

from app.schemas import knowledge_file as kf_schema
from app.crud import crud_knowledge_file, crud_companion
from app.models.user import User
from app.apis.dependencies import get_db, get_current_user

router = APIRouter()

# 定义上传文件的根目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True) # 确保目录存在

@router.post(
    "/companions/{companion_id}/knowledge/upload", 
    response_model=kf_schema.KnowledgeFileRead,
    status_code=status.HTTP_202_ACCEPTED
)
async def upload_knowledge_file(
    *,
    request: Request, # <-- 1. 添加 request 参数来访问 app.state
    companion_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
):
    """
    为指定的 AI 伙伴上传一个新的知识文件。
    """
    # 1. 验证伙伴是否存在且属于当前用户 (这部分逻辑是正确的)
    companion = crud_companion.get_companion_by_id(db=db, companion_id=companion_id)
    if not companion:
        raise HTTPException(status_code=404, detail="Companion not found")
    if companion.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # 2. 保存上传的文件到服务器 (这部分逻辑是正确的)
    try:
        # 使用数据库记录的ID作为目录名，而不是在这里生成
        db_file_id = uuid4()
        file_dir = UPLOAD_DIR / str(current_user.id) / str(db_file_id)
        file_dir.mkdir(parents=True, exist_ok=True)
        file_path = file_dir / file.filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        await file.close()

    # 3. 在数据库中创建文件记录
    file_in = kf_schema.KnowledgeFileCreate(
        id=db_file_id, # 将我们生成的 ID 传入
        file_name=file.filename,
        file_path=str(file_path),
        companion_id=companion_id,
    )
    db_file = crud_knowledge_file.create_knowledge_file(db=db, file_in=file_in)

    # --- ↓↓↓ 4. 这是关键的修改：从 app.state 获取连接池并派发任务 ↓↓↓ ---
    arq_pool: ArqRedis = request.app.state.arq_pool
    await arq_pool.enqueue_job("process_file_task", db_file.id)
    print(f"--- [UPLOAD] Enqueued job 'process_file_task' for file_id: {db_file.id} ---")
    # --- ↑↑↑ 修改结束 ↑↑↑ ---

    return db_file