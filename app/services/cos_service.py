# app/services/cos_service.py

from qcloud_cos import CosConfig, CosS3Client
from app.core.config import settings
from typing import Dict
import logging

# 配置日志记录器
logger = logging.getLogger(__name__)

class COSService:
    """
    一个封装了腾讯云对象存储(COS)所有操作的服务类。
    """
    def __init__(self):
        """
        初始化COS服务。
        在实例化时，会从配置中加载密钥和区域信息，并创建一个COS客户端。
        如果关键配置缺失，将抛出异常，防止服务在不完整的状态下运行。
        """
        # 1. 安全检查：确保所有必要的配置都已提供
        required_configs = [
            settings.COS_SECRET_ID,
            settings.COS_SECRET_KEY,
            settings.COS_REGION,
            settings.COS_BUCKET,
            settings.COS_DOMAIN
        ]
        if not all(required_configs):
            logger.error("COS_SECRET_ID, COS_SECRET_KEY, COS_REGION, COS_BUCKET, and COS_DOMAIN must be configured.")
            raise ValueError("COS service is not properly configured. Please check your .env file.")

        # 2. 创建COS客户端实例
        config = CosConfig(
            Region=settings.COS_REGION,
            SecretId=settings.COS_SECRET_ID,
            SecretKey=settings.COS_SECRET_KEY,
            Scheme='https'  # 推荐使用 https
        )
        self.client = CosS3Client(config)
        self.bucket = settings.COS_BUCKET
        self.domain = str(settings.COS_DOMAIN) # Pydantic HttpUrl 转为 str

    def generate_presigned_url_for_put(self, filename: str) -> Dict[str, str]:
        """
        为客户端生成一个用于HTTP PUT上传的预签名URL。

        Args:
            filename (str): 用户希望上传的文件名。

        Returns:
            Dict[str, str]: 包含 'upload_url' 和 'access_url' 的字典。
                - 'upload_url': 客户端应向其PUT文件的临时授权URL。
                - 'access_url': 文件上传成功后，可用于永久访问的公共URL。
        """
        # 3. 定义对象在存储桶中的完整路径（Key）
        # 我们将所有头像文件统一存放在 'avatars/' 目录下，便于管理
        object_key = f"avatars/{filename}"

        # 4. 调用SDK生成预签名URL
        upload_url = self.client.get_presigned_url(
            Bucket=self.bucket,
            Key=object_key,
            Method='PUT',
            Expired=300  # 预签名URL的有效期，单位：秒。5分钟足够客户端完成上传。
        )

        # 5. 构建最终可公开访问的URL
        # 这个URL是上传成功后，我们存储在数据库里的地址
        access_url = f"{self.domain}/{object_key}"

        return {
            "upload_url": upload_url,
            "access_url": access_url
        }

# 创建一个服务实例，以便在应用的其他地方可以方便地导入和使用
# 这利用了Python模块的单例特性
cos_service = COSService()