# alembic/env.py (最终版)
import sys
from pathlib import Path

# 将项目的根目录添加到 Python 的模块搜索路径中
sys.path.append(str(Path(__file__).resolve().parents[1]))

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# --- 核心修改：只从 app.db.base 导入 Base ---
# 因为 app/db/base.py 已经导入了所有模型，
# 所以这里的 Base.metadata 就包含了所有表的信息。
from app.db.base import Base
from app.core.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)
target_metadata = Base.metadata

print("--- Alembic Detected Tables ---")
print(target_metadata.tables.keys())
print("-----------------------------")

def run_migrations_offline() -> None:
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