# app/apis/v1/chat.py
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
    # 校验：确保伙伴存在且用户有权限连接
    companion = await crud_companion.get_companion_by_id(db=db, companion_id=companion_id)
    if not companion or companion.user_id != current_user.id:
        await websocket.close(code=status.WS_1007_INVALID_FRAMEWORK_PAYLOAD, reason="Companion not found or access denied")
        return

    await websocket.accept()

    # 只传递 companion_id（标量）给 ChatService，避免持有 ORM 实例导致干扰
    chat_service = ChatService(
        db=db,
        redis_client=redis_client,
        companion_id=companion_id,
        user_id=current_user.id
    )

    # 预存安全的日志变量（避免在断开连接或异常处理时访问 ORM 实例）
    current_user_id_for_log = current_user.id
    companion_name_for_log = companion.name

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
        print(f"Client {current_user_id_for_log} disconnected from chat with {companion_name_for_log}")

    except Exception as e:
        print(f"--- An unexpected error occurred in WebSocket for user {current_user_id_for_log} ---")
        traceback.print_exc()
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
