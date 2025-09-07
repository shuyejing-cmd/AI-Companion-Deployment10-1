# tests/conftest.py (最终版)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.config import settings
from app.apis.dependencies import get_db
from app.db.base import Base

# --- 1. 定义一个全局的测试数据库引擎 ---
# 我们仍然使用文件型数据库，因为它最稳定可靠
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --- 2. 创建一个在所有测试运行前后执行一次的 'session' 级 fixture ---
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    这个 fixture 会在整个测试会话开始时运行一次，结束时清理一次。
    `autouse=True` 意味着所有测试都会自动使用它，无需手动指定。
    """
    # --- 测试开始前 ---
    # a. 确保所有模型都已加载
    assert Base.metadata.tables, "Models not loaded, Base.metadata is empty!"
    # b. 在测试数据库中创建所有表
    Base.metadata.create_all(bind=engine)
    
    yield  # <-- 所有测试将在这里运行
    
    # --- 测试结束后 ---
    # a. 删除所有表
    Base.metadata.drop_all(bind=engine)


# --- 3. 创建一个为每个测试函数服务的 client fixture ---
@pytest.fixture(scope="function")
def client():
    """
    为每个测试提供一个干净的 TestClient 实例。
    """
    def override_get_db():
        """依赖覆盖函数：从测试引擎创建会话"""
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # 应用依赖覆盖
    app.dependency_overrides[get_db] = override_get_db
    
    # 临时修改Redis配置
    original_redis_host = settings.REDIS_HOST
    settings.REDIS_HOST = "localhost"

    # 生成并返回客户端
    yield TestClient(app)

    # 清理工作
    settings.REDIS_HOST = original_redis_host
    app.dependency_overrides.clear()