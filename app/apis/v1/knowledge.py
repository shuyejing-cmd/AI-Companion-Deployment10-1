from uuid import UUID
from pathlib import Path
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from uuid import UUID, uuid4 as UUID_v4

from app.schemas import knowledge_file as kf_schema
from app.crud import crud_knowledge_file, crud_companion
from app.models.user import User
from app.apis.dependencies import get_db, get_current_user
from sqlalchemy.orm import Session

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
    companion_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
):
    """
    为指定的 AI 伙伴上传一个新的知识文件。
    """
    # 1. 验证伙伴是否存在且属于当前用户
    companion = crud_companion.get_companion_by_id(db=db, companion_id=companion_id)
    if not companion:
        raise HTTPException(status_code=404, detail="Companion not found")
    if companion.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # 2. 保存上传的文件到服务器
    try:
        # 创建一个唯一的子目录来存放文件，避免文件名冲突
        file_id = UUID_v4() #生成一个唯一的id
        file_dir = UPLOAD_DIR / str(file_id)
        file_dir.mkdir()
        file_path = file_dir / file.filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
    finally:
        file.file.close()

    # 3. 在数据库中创建文件记录
    file_in = kf_schema.KnowledgeFileCreate(
        file_name=file.filename,
        file_path=str(file_path),
        companion_id=companion_id,
    )
    db_file = crud_knowledge_file.create_knowledge_file(db=db, file_in=file_in)

    # 4. TODO: 在这里触发一个 ARQ 后台任务
    # from app.core.arq_worker import arq_pool
    # await arq_pool.enqueue_job("process_file_task", db_file.id)

    return db_file