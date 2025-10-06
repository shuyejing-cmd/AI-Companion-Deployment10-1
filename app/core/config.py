# app/core/config.py

from typing import Dict, Any, Optional
from pydantic import Field, HttpUrl, validator # 确保导入了 validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # --- 基础配置 ---
    PROJECT_NAME: str = "My AI Companion Backend"
    DATABASE_URL: str
    API_V1_STR: str = "/api/v1"
    
    # --- 安全性配置 ---
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # --- AI & 向量数据库配置 ---
    OPENAI_API_KEY: str
    DEEPSEEK_API_BASE: str
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str
    
    # --- Redis 配置 ---
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int

    # 🚀 --- 关键修复：新增异步数据库URL配置 ---
    ASYNC_DATABASE_URL: Optional[str] = None

    @validator("ASYNC_DATABASE_URL", pre=False, always=True)
    def set_async_database_url(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        """
        根据 DATABASE_URL 自动生成异步数据库连接字符串。
        """
        if isinstance(v, str):
            # 如果 .env 中已明确设置，则直接使用
            return v
        
        db_url = values.get("DATABASE_URL")
        if db_url:
            # 将 "postgresql://" 替换为 "postgresql+asyncpg://"
            return db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        raise ValueError("DATABASE_URL must be set")
    # 🚀 --- 修复结束 ---

    # --- 腾讯云 COS 配置 ---
    COS_SECRET_ID: str = Field("", validation_alias="COS_SECRET_ID")
    COS_SECRET_KEY: str = Field("", validation_alias="COS_SECRET_KEY")
    COS_REGION: str = Field("ap-shanghai")
    COS_BUCKET: str = Field("")
    COS_DOMAIN: Optional[HttpUrl] = Field(None)
    # ---

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    def get_redis_settings(self) -> Dict[str, Any]:
        return {
            'host': self.REDIS_HOST,
            'port': self.REDIS_PORT,
            'database': self.REDIS_DB,
        }

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore"
    )

settings = Settings()