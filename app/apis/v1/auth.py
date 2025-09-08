# app/apis/v1/auth.py (适配异步版)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.schemas import user as user_schema
from app.crud import crud_user
from app.apis.dependencies import get_db
from app.core.security import create_jwt_for_user

router = APIRouter()

class WechatLoginRequest(BaseModel):
    code: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# 关键改动：端点函数也改为 async def
@router.post("/auth/wechat", response_model=TokenResponse)
async def login_wechat( # <-- 变为 async
        *,
        request_body: WechatLoginRequest,
        db: Session = Depends(get_db)
    ):
        if not request_body.code:
            raise HTTPException(status_code=400, detail="Code is required")
        
        fake_openid = f"fake_openid_for_{request_body.code}"

        # 关键改动：使用 await 来调用异步的CRUD函数
        user = await crud_user.get_user_by_openid(db=db, openid=fake_openid)

        if not user:
            user_in = user_schema.UserCreate(openid=fake_openid)
            user = await crud_user.create_user(db=db, user_in=user_in)
        
        access_token = create_jwt_for_user(user.id)
        return {"access_token": access_token, "token_type": "bearer"}