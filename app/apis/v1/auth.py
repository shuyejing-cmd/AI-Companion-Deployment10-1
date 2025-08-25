from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.schemas import user as user_schema
from app.crud import crud_user
from app.apis.dependencies import get_db
from app.core.security import create_jwt_for_user

router = APIRouter()

    # 定义请求体模型
class WechatLoginRequest(BaseModel):
    code: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

@router.post("/auth/wechat", response_model=TokenResponse)
def login_wechat(
        *,
        request_body: WechatLoginRequest,
        db: Session = Depends(get_db)
    ):
        """
        处理微信登录请求
        """
        # --- 模拟与微信服务器交互 ---
        # TODO: 在未来，这里需要用 request_body.code 去请求微信的 code2Session 接口
        # 目前，我们为了测试，直接从 code 伪造一个 openid
        if not request_body.code:
            raise HTTPException(status_code=400, detail="Code is required")
        
        # 伪造 openid 用于测试
        fake_openid = f"fake_openid_for_{request_body.code}"
        # --- 模拟结束 ---

        # 1. 尝试根据 openid 查找用户
        user = crud_user.get_user_by_openid(db=db, openid=fake_openid)

        # 2. 如果用户不存在，则创建新用户 (自动注册)
        if not user:
            user_in = user_schema.UserCreate(openid=fake_openid)
            user = crud_user.create_user(db=db, user_in=user_in)
        
        # TODO: 在未来，这里需要生成并返回一个 JWT token
        
        access_token = create_jwt_for_user(user.id)
        return {"access_token": access_token, "token_type": "bearer"}