import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import crud_user
from app.schemas.user import UserCreate

# 注意：CRUD 操作现在是同步的，但可以在异步测试中运行
# 为了未来的兼容性，最好将CRUD也改为异步，但目前这样也能工作
@pytest.mark.asyncio
async def test_create_and_get_user(db_session: AsyncSession):
    test_openid = "test-openid-123"
    user_in = UserCreate(openid=test_openid)
    
    # SQLAlchemy 2.0 允许在异步会话中运行同步风格的 ORM 代码
    created_user = crud_user.create_user(db=db_session, user_in=user_in)
    assert created_user is not None
    
    retrieved_user = crud_user.get_user_by_openid(db=db_session, openid=test_openid)
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id