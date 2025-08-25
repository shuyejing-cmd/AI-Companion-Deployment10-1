from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate

def get_user_by_openid(db: Session, openid: str) -> User | None:
    """
    通过 openid 查询用户
    """
    return db.query(User).filter(User.openid == openid).first()

def create_user(db: Session, user_in: UserCreate) -> User:
    """
    创建一个新用户
    """
    # 将 Pydantic 模型转换为 SQLAlchemy 模型可以理解的字典
    db_user = User(**user_in.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user) # 刷新实例，以获取数据库自动生成的值 (如 id, created_at)
    return db_user