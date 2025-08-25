from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # --- FastAPI App Settings ---
    PROJECT_NAME: str = "AI Companion Backend"
    API_V1_STR: str = "/api/v1"

    # --- Database Settings ---
    DATABASE_URL: str
    # --- 核心修改：添加这三个字段 ---
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    # --- Redis Settings ---
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int

    # --- JWT Settings ---
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # --- AI & Vector DB Settings ---
    OPENAI_API_KEY: str
    DEEPSEEK_API_BASE: str
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

settings = Settings()
