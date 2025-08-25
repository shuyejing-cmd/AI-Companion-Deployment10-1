from contextlib import asynccontextmanager
import redis.asyncio as redis
from fastapi import FastAPI

from app.core.config import settings
from app.apis.v1 import auth as auth_router
from app.apis.v1 import companions as companion_router
from app.apis.v1 import chat as chat_router
from app.apis.v1 import knowledge as knowledge_router 

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup...")
    redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
    print(f"Connecting to Redis at: {redis_url}")
    app.state.redis_pool = redis.ConnectionPool.from_url(redis_url, decode_responses=False)
    print("Redis connection pool created and stored in app.state.")
    yield
    print("Application shutdown...")
    if hasattr(app.state, 'redis_pool') and app.state.redis_pool:
        await app.state.redis_pool.disconnect()
        print("Redis connection pool disconnected.")

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.include_router(auth_router.router, prefix=settings.API_V1_STR, tags=["Authentication"])
app.include_router(companion_router.router, prefix=f"{settings.API_V1_STR}/companions", tags=["Companions"])
app.include_router(chat_router.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat"])
app.include_router(knowledge_router.router, prefix=f"{settings.API_V1_STR}", tags=["Knowledge"])

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}