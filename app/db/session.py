# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


# --- 同步数据库引擎和会话 ---
# Alembic 和同步的 API 依赖项 (比如 get_db) 需要这个
sync_engine = create_engine(
    settings.DATABASE_URL, # 使用标准的 DATABASE_URL
    pool_pre_ping=True
)
# 定义同步会话工厂 SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# 创建异步引擎
async_engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600 # 推荐添加，避免连接长时间闲置后失效
)

# 创建异步会话工厂 (AsyncSessionLocal)
AsyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession
)