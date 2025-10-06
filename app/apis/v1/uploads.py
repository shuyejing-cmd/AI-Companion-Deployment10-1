# app/apis/v1/uploads.py

import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.upload import PresignedUrlRequest, PresignedUrlResponse
from app.schemas.user import User
from app.services.cos_service import cos_service
from app.apis.dependencies import get_current_user

# 配置日志记录器
logger = logging.getLogger(__name__)

# 创建一个新的API路由器实例
router = APIRouter()

@router.post(
    "/avatar/presigned-url",
    response_model=PresignedUrlResponse,
    summary="获取头像上传的预签名URL"
)
async def get_presigned_url_for_avatar(
    request_body: PresignedUrlRequest,
    current_user: User = Depends(get_current_user)
):
    """
    为当前登录用户获取一个用于上传头像的预签名URL。

    - **必须是认证用户** 才能访问此接口。
    - 前端需提供原始文件名 `filename` 和文件类型 `content_type`。
    - 后端将生成一个唯一的、安全的文件名来存储文件。
    """
    try:
        # 1. 安全性：从原始文件名中提取文件扩展名
        # 我们不直接使用用户提供的文件名，以防止路径注入等安全风险。
        try:
            file_extension = request_body.filename.split('.')[-1]
        except IndexError:
            raise HTTPException(status_code=400, detail="Invalid filename, missing extension.")

        # 2. 生成一个唯一的、不会冲突的文件名
        # 格式：[用户ID]_[UUID].[原始扩展名]
        unique_filename = f"{current_user.id}_{uuid.uuid4()}.{file_extension}"

        # 3. 调用我们封装好的COSService来生成URL
        presigned_data = cos_service.generate_presigned_url_for_put(
            filename=unique_filename
        )
        
        return presigned_data

    except ValueError as e:
        # 这个异常来自于我们的COSService初始化失败
        logger.error(f"COS Service Configuration Error: {e}")
        raise HTTPException(status_code=500, detail="Upload service is not configured.")
    except Exception as e:
        # 捕获其他潜在的错误，例如腾讯云SDK的运行时错误
        logger.error(f"Failed to generate presigned URL for user {current_user.email}: {e}")
        raise HTTPException(status_code=500, detail="Could not generate upload URL.")