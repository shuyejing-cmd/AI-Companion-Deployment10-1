# app/core/config.py

from pydantic_settings import BaseSettings
from typing import Dict, Any

class Settings(BaseSettings):
    # --- 你已有的所有配置项 ---
    PROJECT_NAME: str = "My AI Companion Backend"
    DATABASE_URL: str
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    OPENAI_API_KEY: str
    DEEPSEEK_API_BASE: str
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str
    
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int

    @property
    def REDIS_URL(self) -> str:
        """
        根据已加载的 HOST, PORT, DB 自动拼接成完整的 Redis 连接 URL。
        """
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # --- ↓↓↓ 我们需要新增的方法 ↓↓↓ ---
    def get_redis_settings(self) -> Dict[str, Any]:
        """
        生成 ARQ 期望的 Redis 配置字典。
        """
        return {
            'host': self.REDIS_HOST,
            'port': self.REDIS_PORT,
            'database': self.REDIS_DB,
        }
    # --- ↑↑↑ 我们需要新增的方法 ↑↑↑ ---

    # --- ↓↓↓ (可选，但推荐) 异步数据库 URL ---
    # 我们之前的 KnowledgeService 也需要这个
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        # 确保 psycopg2 驱动被替换为 asyncpg
        if self.DATABASE_URL.startswith("postgresql+psycopg2://"):
            return self.DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
        return self.DATABASE_URL # 如果已经是其他格式，直接返回
    # --- ↑↑↑ (可选，但推荐) 异步数据库 URL ---

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

# 创建全局 settings 实例
settings = Settings()
