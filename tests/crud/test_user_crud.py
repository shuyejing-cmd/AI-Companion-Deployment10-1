# tests/crud/test_user_crud.py (异步版，最佳实践)
import pytest
from app.crud import crud_user
from app.schemas.user import UserCreate
from tests.conftest import TestingSessionLocal 

@pytest.mark.asyncio
async def test_create_and_get_user():
    db = TestingSessionLocal()
    try:
        test_openid = "test-openid-123"
        user_in = UserCreate(openid=test_openid)
        created_user = crud_user.create_user(db=db, user_in=user_in)
        assert created_user is not None
        retrieved_user = crud_user.get_user_by_openid(db=db, openid=test_openid)
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
    finally:
        db.close()