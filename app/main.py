import redis.asyncio as redis
from fastapi import FastAPI
from arq.connections import create_pool, RedisSettings

from app.core.config import settings
from app.apis.v1 import auth as auth_router
from app.apis.v1 import companions as companions_router
from app.apis.v1 import chat as chat_router
from app.apis.v1 import knowledge as knowledge_router

app = FastAPI(title=settings.PROJECT_NAME)

@app.on_event("startup")
async def startup_event():
    print("--- Application startup... ---")
    
    arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    app.state.arq_pool = arq_pool
    print("ARQ Redis pool created.")

    print(f"Creating general Redis client at: {settings.REDIS_URL}")
    redis_client = redis.from_url(
        settings.REDIS_URL, 
        encoding="utf-8"
    )
    
    # --- 【【【关键修复：存储正确的东西，并使用正确的标签】】】 ---
    # 我们将 redis_client 的 connection_pool 属性
    # 存储到 app.state.redis_pool 中
    app.state.redis_pool = redis_client.connection_pool
    # --- 修复结束 ---
    
    # 我们仍然需要客户端本身，以便在关闭时调用 .close()
    app.state.redis_client = redis_client 
    print("General Redis connection pool created.")

@app.on_event("shutdown")
async def shutdown_event():
    print("--- Application shutdown... ---")
    if hasattr(app.state, 'arq_pool'):
        await app.state.arq_pool.close()
        print("ARQ Redis pool closed.")
    if hasattr(app.state, 'redis_client'):
        if hasattr(app.state.redis_client, 'close'):
             await app.state.redis_client.close()
        print("General Redis client closed.")

# 路由挂载
app.include_router(auth_router.router, prefix=settings.API_V1_STR, tags=["Authentication"])
app.include_router(companions_router.router, prefix=f"{settings.API_V1_STR}/companions", tags=["Companions"])
app.include_router(chat_router.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat"])
app.include_router(knowledge_router.router, prefix=settings.API_V1_STR, tags=["Knowledge"])

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}