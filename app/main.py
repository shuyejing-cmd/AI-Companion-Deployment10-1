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
    
    # --- ↓↓↓ 核心修改: 将 redis_client 实例直接存入 app.state ↓↓↓ ---
    # 这样，任何依赖项都可以通过 app.state.redis_client 来获取它
    app.state.redis_client = redis_client
    print("General Redis client stored in app.state.")
    # --- 修改结束 ---

@app.on_event("shutdown")
async def shutdown_event():
    print("--- Application shutdown... ---")
    if hasattr(app.state, 'arq_pool'):
        await app.state.arq_pool.close()
        print("ARQ Redis pool closed.")
    
    # 直接从 app.state 获取并关闭，逻辑更清晰
    if hasattr(app.state, 'redis_client'):
        await app.state.redis_client.close()
        print("General Redis client closed.")


# 路由挂载 (保持不变)
app.include_router(auth_router.router, prefix=settings.API_V1_STR, tags=["Authentication"])
app.include_router(companions_router.router, prefix=f"{settings.API_V1_STR}/companions", tags=["Companions"])
app.include_router(chat_router.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat"])
app.include_router(knowledge_router.router, prefix=settings.API_V1_STR, tags=["Knowledge"])

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}