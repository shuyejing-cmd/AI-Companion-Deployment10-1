from app.core.config import settings

# 导入我们未来将要创建的任务函数
# from app.services.knowledge_service import process_file_task, delete_vectors_task

class WorkerSettings:
    """
    ARQ Worker 的配置类。
    """
    # 指定要执行的任务函数列表
    # functions = [process_file_task, delete_vectors_task] # <-- 现在先注释掉，因为还没创建
    functions = []
    
    # 使用我们 .env 文件中的 Redis 配置来连接到任务队列
    redis_settings = {
        'host': settings.REDIS_HOST,
        'port': settings.REDIS_PORT,
        'database': settings.REDIS_DB,
    }

    # 当 arq worker 启动时，会自动读取这个类的配置