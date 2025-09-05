#!/bin/sh
set -e

# --- 增加健壮性：为环境变量提供默认值 ---
# 如果 POSTGRES_HOST 变量不存在或为空，就使用 'db' 作为默认值
DB_HOST=${POSTGRES_HOST:-db}
DB_PORT=${POSTGRES_PORT:-5432}
DB_USER=${POSTGRES_USER:-postgres}
# ------------------------------------------

# --- 增加调试信息，方便排查 ---
echo "--- Starting Entrypoint Script ---"
echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
# ------------------------------------

# 等待 PostgreSQL 服务启动
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 3
done

echo "PostgreSQL is up - executing migrations"

# 运行 Alembic 迁移
python -m alembic upgrade head

echo "Migrations complete - starting application"


exec "$@"
