import traceback
from typing import List
from uuid import UUID
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.models.user import User
from app.schemas import message as message_schema
from app.crud import crud_message, crud_companion
from app.apis.dependencies import (
    get_async_db,
    get_redis_client_ws,
    get_current_user_from_token,
    get_current_user
)
from app.services.chat_service import ChatService

router = APIRouter()

@router.get(
    "/messages/{companion_id}",
    response_model=List[message_schema.MessageRead],
    summary="获取历史聊天记录"
)
async def read_messages(
    companion_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    messages = await crud_message.get_messages_by_companion_ascending(
        db=db,
        companion_id=companion_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return messages


@router.websocket("/ws/{companion_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    companion_id: UUID,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_async_db),
    redis_client: redis.Redis = Depends(get_redis_client_ws)
):
    companion = await crud_companion.get_companion_by_id(db=db, companion_id=companion_id)
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

    # --- 【【【终极修复：数据预加载】】】 ---
    # 在进入主循环之前，将所有可能在异常处理中用到的数据从数据库对象中取出，存入普通变量。
    # 这样可以确保在 WebSocketDisconnect 等不稳定的上下文中，我们不会进行任何数据库IO。
    current_user_id_for_log = current_user.id
    companion_name_for_log = companion.name
    # --- 修复结束 ---

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
        # 【【【终极修复：只使用预加载的、安全的变量来打印日志】】】
        print(f"Client {current_user_id_for_log} disconnected from chat with {companion_name_for_log}")

    except Exception as e:
        # 增加对其他未知异常的日志记录
        print(f"--- An unexpected error occurred in WebSocket for user {current_user_id_for_log} ---")
        traceback.print_exc()
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)