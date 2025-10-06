# app/schemas/upload.py

from pydantic import BaseModel, HttpUrl

class PresignedUrlRequest(BaseModel):
    """
    前端请求预签名URL时需要提供的数据模型 (契约)。
    """
    filename: str
    content_type: str

class PresignedUrlResponse(BaseModel):
    """
    后端返回给前端的预签名URL和最终访问URL的数据模型 (契约)。
    """
    upload_url: HttpUrl  # 用于PUT上传的预签名URL
    access_url: HttpUrl  # 上传成功后，用于存储和访问的永久URL