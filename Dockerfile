# Dockerfile
# --------------------------------------------------

# 使用官方的 Python 3.10 slim 镜像作为基础
FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client && rm -rf /var/lib/apt/lists/*
# --- 1. 设置关键环境变量 ---
#    确保 Python 的输出日志不会被缓冲，可以实时看到
ENV PYTHONUNBUFFERED=1
#    定义虚拟环境的路径，方便后续引用
ENV VIRTUAL_ENV=/.venv
#    创建虚拟环境
RUN python -m venv $VIRTUAL_ENV

# --- 2. 【【【 这是解决问题的核心 】】】 ---
#    将虚拟环境的 bin 目录添加到系统 PATH 环境变量的最前面。
#    这样，后续所有命令（如 python, pip, alembic）都会自动使用虚拟环境中的版本。
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# --- 3. 设置工作目录 ---
WORKDIR /app

# --- 4. 复制并安装依赖 ---
#    因为第 2 步的 PATH 设置，这里的 pip 命令会自动指向 /.venv/bin/pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./download_model.py /app/download_model.py
RUN python /app/download_model.py

# --- 5. 复制所有项目代码 ---
COPY . .

# --- 6. 确保入口脚本有执行权限 ---
#    这是一个好习惯，可以避免权限问题
RUN chmod +x /app/entrypoint.sh

# --- 7. 设置入口点脚本 ---
ENTRYPOINT ["/app/entrypoint.sh"]

# --- 8. 为 app 服务设置默认的启动命令 ---
#    worker 服务的命令会在 docker-compose.yml 中被覆盖
CMD ["python", "-m", "hypercorn", "app.main:app", "--bind", "0.0.0.0:8000"]

# --------------------------------------------------