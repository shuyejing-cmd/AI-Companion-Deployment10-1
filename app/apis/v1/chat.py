# app/apis/v1/chat.py (最终修正版)

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
import redis.asyncio as redis

from app.models.user import User
# --- 关键改动: 导入正确的依赖项 ---
from app.apis.dependencies import (
    get_db,
    get_redis_client_ws,
    get_current_user_from_token
)
from app.services.chat_service import ChatService
from app.crud import crud_companion

router = APIRouter()

@router.websocket("/ws/{companion_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    companion_id: UUID,
    # --- 关键改动: 使用 FastAPI 的依赖注入来优雅地处理认证 ---
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client_ws)
):
    # 如果代码能执行到这里，就说明 current_user 一定是有效的。
    
    companion = crud_companion.get_companion_by_id(db=db, companion_id=companion_id)
    if not companion:
        await websocket.close(code=status.WS_1007_INVALID_FRAMEWORK_PAYLOAD, reason="Companion not found")
        return

    await websocket.accept()
    
    chat_service = ChatService(
        db=db, 
        redis_client=redis_client, 
        companion=companion, 
        user_id=current_user.id
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
        print(f"Client {current_user.id} disconnected from chat with {companion.name}")
    except Exception:
        print("--- Error in main WebSocket loop ---")
        traceback.print_exc()
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)