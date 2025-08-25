#!/bin/sh
# 使用 /bin/sh 确保更好的兼容性

set -e

echo "Waiting for PostgreSQL to be ready..."

# 使用 pg_isready 循环等待数据库准备就绪
until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER"; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 3
done

echo "PostgreSQL is up - executing migrations"

# 自动生成迁移（如果需要）并应用
alembic upgrade head

echo "Migrations check complete - starting application"

exec hypercorn app.main:app --bind 0.0.0.0:8000