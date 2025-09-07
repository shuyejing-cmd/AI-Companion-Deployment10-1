from app.crud import crud_user
from app.schemas.user import UserCreate
# 关键：从 conftest 导入测试专用的 Session 工厂
from tests.conftest import TestingSessionLocal 

def test_create_and_get_user():
    # 每个CRUD测试都从测试工厂获取一个独立的会话
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