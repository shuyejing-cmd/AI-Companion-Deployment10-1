import sys
from pathlib import Path

# 将项目根目录 (ai-companion-backend) 添加到 Python 的模块搜索路径中
# Path(__file__) -> D:\...\ai-companion-backend\alembic\env.py
# .resolve() -> 获取绝对路径
# .parents[1] -> 获取上级目录，即 ai-companion-backend
# str(...) -> 转换为字符串路径
sys.path.append(str(Path(__file__).resolve().parents[1]))


from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# --- 现在我们可以安全地从 app 模块导入我们的配置和模型了 ---
from app.core.config import settings
from app.db.base_class import Base
# 导入所有需要被 Alembic 追踪的模型
from app.models.user import User
from app.models.companion import Companion
from app.models.message import Message
from app.models.knowledge_file import KnowledgeFile


# 这是 Alembic 的配置对象，提供了对 .ini 文件值的访问
config = context.config

# 为 Python 日志解释配置文件
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- 核心修改：用我们从 .env 加载的配置覆盖 .ini 文件中的 sqlalchemy.url ---
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)


# 在这里设置你的模型的 Base 类，以便 autogenerate 可以找到它们
target_metadata = Base.metadata

# 其他来自配置的值，可以按需获取
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """在 'offline' 模式下运行迁移。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在 'online' 模式下运行迁移。"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()