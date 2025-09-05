# app/main.py (最终兼容版)

import redis.asyncio as redis
from fastapi import FastAPI
from arq.connections import create_pool, RedisSettings

from app.core.config import settings
from app.apis.v1 import auth as auth_router
from app.apis.v1 import companions as companions_router
from app.apis.v1 import chat as chat_router
from app.apis.v1 import knowledge as knowledge_router

# 1. 先创建 FastAPI 应用实例
app = FastAPI(title=settings.PROJECT_NAME)

# --- 使用 on_event 装饰器来定义启动和关闭事件 ---

@app.on_event("startup")
async def startup_event():
    """
    应用启动时执行的异步函数
    """
    print("--- Application startup... ---")
    
    # 创建并存储 ARQ 任务队列专用的连接池
    print(f"Creating ARQ Redis pool at: {settings.REDIS_URL}")
    arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    app.state.arq_pool = arq_pool
    print("ARQ Redis pool created.")

    # 创建并存储通用的 redis-py 连接池，用于 WebSocket 等
    print(f"Creating general Redis client at: {settings.REDIS_URL}")
    redis_client = redis.from_url(
        settings.REDIS_URL, 
        encoding="utf-8", 
        decode_responses=True
    )
    app.state.redis_pool = redis_client.connection_pool
    # 将客户端本身也存起来，以便在关闭时调用 .close()
    app.state.redis_client = redis_client 
    print("General Redis connection pool created.")

@app.on_event("shutdown")
async def shutdown_event():
    """
    应用关闭时执行的异步函数
    """
    print("--- Application shutdown... ---")
    if hasattr(app.state, 'arq_pool'):
        await app.state.arq_pool.close()
        print("ARQ Redis pool closed.")
    if hasattr(app.state, 'redis_client'):
        await app.state.redis_client.close()
        print("General Redis client closed.")

# --- 修改结束 ---

# 2. 挂载你的 API 路由
app.include_router(auth_router.router, prefix=settings.API_V1_STR, tags=["Authentication"])
app.include_router(companions_router.router, prefix=f"{settings.API_V1_STR}/companions", tags=["Companions"])
app.include_router(chat_router.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat"])
app.include_router(knowledge_router.router, prefix=settings.API_V1_STR, tags=["Knowledge"])

# 根路径的端点，用于简单的健康检查
@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}