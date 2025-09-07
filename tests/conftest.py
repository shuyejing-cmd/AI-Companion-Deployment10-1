# tests/conftest.py (最终完美异步版)

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 关键：导入 app, settings, Base, 和原始的 get_db 依赖
from app.main import app
from app.core.config import settings
from app.db.base import Base
from app.apis.dependencies import get_db

# --- 1. 创建一个异步的测试数据库引擎 ---
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
async_engine = create_async_engine(TEST_DATABASE_URL)
AsyncTestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession
)

# --- 2. 创建一个异步的、贯穿所有测试的 setup fixture ---
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """
    在整个测试会话开始时，以异步方式创建所有表，并在结束后删除。
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# --- 3. 创建一个异步的数据库会话 fixture ---
@pytest_asyncio.fixture(scope="function")
async def db_session():
    """为每个测试函数提供一个独立的异步数据库会话。"""
    async with AsyncTestingSessionLocal() as session:
        yield session

# --- 4. 创建最终的 client fixture ---
@pytest.fixture(scope="function")
def client(db_session: AsyncSession): # 它依赖于异步的 db_session
    """创建一个配置好的、使用异步测试数据库的API客户端。"""

    def override_get_db():
        """依赖覆盖函数"""
        try:
            yield db_session
        finally:
            pass # 会话由 db_session fixture 管理

    app.dependency_overrides[get_db] = override_get_db
    
    original_redis_host = settings.REDIS_HOST
    settings.REDIS_HOST = "localhost"

    yield TestClient(app)

    settings.REDIS_HOST = original_redis_host
    app.dependency_overrides.clear()