# tests/conftest.py (最终修正版)

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.config import settings
from app.db.base import Base
from app.apis.dependencies import get_db
from app.core.security import create_jwt_for_user
from app.schemas.user import UserCreate
from app.crud import crud_user

# --- 1. 异步测试数据库引擎设置 ---
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
async_engine = create_async_engine(TEST_DATABASE_URL)
AsyncTestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession
)

# --- 2. 自动运行的、异步的数据库准备Fixture ---
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """在所有测试开始前创建表，结束后删除表。"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# --- 3. 提供异步数据库会话的Fixture ---
@pytest_asyncio.fixture(scope="function")
async def db_session():
    """为每个测试提供一个独立的异步数据库会话。"""
    async with AsyncTestingSessionLocal() as session:
        yield session

# --- 4. 提供基础的、未认证的API客户端的Fixture ---
@pytest.fixture(scope="function")
def client(db_session: AsyncSession):
    """
    创建一个基础的、未认证的API客户端，并配置好测试数据库和Redis。
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    original_redis_host = settings.REDIS_HOST
    settings.REDIS_HOST = "localhost"

    yield TestClient(app)

    settings.REDIS_HOST = original_redis_host
    app.dependency_overrides.clear()

# --- 5. 提供“已认证”的API客户端的Fixture ---
@pytest_asyncio.fixture(scope="function")
async def authenticated_client(client: TestClient, db_session: AsyncSession):
    """
    利用基础客户端，创建一个“已认证”的客户端。
    """
    test_user_in = UserCreate(openid="test-authed-user-openid")
    test_user = await crud_user.create_user(db=db_session, user_in=test_user_in)
    
    token = create_jwt_for_user(test_user.id)
    
    client.headers["Authorization"] = f"Bearer {token}"
    
    yield client