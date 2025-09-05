# app/core/arq_worker.py

import logging
from uuid import UUID
from arq import ArqRedis
from arq.connections import create_pool
from app.db import base

from app.core.config import settings
from arq.connections import RedisSettings
# --- ↓↓↓ 关键改动：导入我们刚刚创建的 KnowledgeService ↓↓↓ ---
from app.services.knowledge_service import KnowledgeService

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 全局 ARQ 连接池
arq_pool: ArqRedis | None = None

async def create_arq_pool() -> ArqRedis:
    """创建并返回 ARQ 连接池"""
    global arq_pool
    if arq_pool is None:
        arq_pool = await create_pool(WorkerSettings.redis_settings)
    return arq_pool

async def close_arq_pool():
    """关闭 ARQ 连接池"""
    if arq_pool:
        await arq_pool.close()

# --- ARQ 任务定义 ---

async def process_file_task(ctx, file_id: UUID):
    """
    ARQ 任务：后台处理上传的知识文件。
    ctx 包含了任务的上下文信息，如 redis 连接。
    """
    logging.info(f"Worker 接到任务: process_file_task, file_id: {file_id}")
    try:
        # --- ↓↓↓ 关键改动：实例化服务并调用核心逻辑 ↓↓↓ ---
        knowledge_service = KnowledgeService()
        await knowledge_service.process_and_index_file(file_id)
        logging.info(f"成功完成任务, file_id: {file_id}")
    except Exception as e:
        # 这里的日志主要用于捕获服务实例化等更高层的错误
        logging.error(f"执行任务 process_file_task (file_id: {file_id}) 时发生致命错误: {e}", exc_info=True)
        # 具体的错误处理和数据库状态更新，已经在 KnowledgeService 内部完成

# --- Worker 配置 ---

class WorkerSettings:
    """
    ARQ Worker 的配置类。
    """
    # --- ↓↓↓ 关键改动：注册我们的任务函数 ↓↓↓ ---
    functions = [process_file_task]
    
    redis_settings = RedisSettings(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    database=settings.REDIS_DB
)
    
    # 任务执行的超时时间，例如 10 分钟
    job_timeout = 600