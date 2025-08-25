import traceback
from uuid import UUID
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    status,
)
from sqlalchemy.orm import Session
from jose import jwt, JWTError
import redis.asyncio as redis

from app.core.config import settings
from app.models.user import User
from app.apis.dependencies import get_db, get_redis_client_ws # <-- 导入新的依赖项
from app.services.chat_service import ChatService
from app.crud import crud_companion

router = APIRouter()

async def get_current_user_from_token(token: str, db: Session) -> User | None:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None: return None
        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    return user

@router.websocket("/ws/{companion_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    companion_id: UUID,
    token: str,
    db: Session = Depends(get_db),
    # --- 核心修改：使用新的、专门为 WebSocket 设计的依赖项 ---
    redis_client: redis.Redis = Depends(get_redis_client_ws)
):
    user = await get_current_user_from_token(token, db)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    companion = crud_companion.get_companion_by_id(db=db, companion_id=companion_id)
    if not companion:
        await websocket.close(code=status.WS_1007_INVALID_FRAMEWORK_PAYLOAD, reason="Companion not found")
        return

    await websocket.accept()
    
    # 将通过依赖注入获取的、有效的 redis_client 传递给 ChatService
    chat_service = ChatService(
        db=db, 
        redis_client=redis_client, 
        companion=companion, 
        user_id=user.id
    )

    try:
        while True:
            user_message = await websocket.receive_text()
            try:
                async for ai_token in chat_service.process_user_message(user_message):
                    await websocket.send_text(ai_token)
                await websocket.send_text("[END_OF_STREAM]")
            except Exception:
                print("--- Error during chat processing ---")
                traceback.print_exc()
                await websocket.send_text("[ERROR] An internal error occurred.")
                await websocket.send_text("[END_OF_STREAM]")

    except WebSocketDisconnect:
        print(f"Client {user.id} disconnected from chat with {companion.name}")
    except Exception:
        print("--- Error in main WebSocket loop ---")
        traceback.print_exc()
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)