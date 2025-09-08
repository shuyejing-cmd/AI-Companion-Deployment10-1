# tests/crud/test_user_crud.py (最终修正版)

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import crud_user
from app.schemas.user import UserCreate

@pytest.mark.asyncio
async def test_create_and_get_user(db_session: AsyncSession):
    test_openid = "test-openid-123"
    user_in = UserCreate(openid=test_openid)

    # 关键改动：使用 await 来“兑现”异步函数的承诺
    created_user = await crud_user.create_user(db=db_session, user_in=user_in)
    assert created_user is not None

    # 关键改动：同样需要 await
    retrieved_user = await crud_user.get_user_by_openid(db=db_session, openid=test_openid)
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id