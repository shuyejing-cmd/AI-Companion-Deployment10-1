FROM python:3.10-slim

# --- 核心修改：在执行 apt-get 之前，先替换软件源为国内镜像 ---
# 备份原始源列表
RUN mv /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list.d/debian.sources.bak
# 创建新的源列表文件，并写入阿里云的 Debian 镜像源地址
# 注意：我们基础镜像是 Debian Trixie (testing/unstable)，所以用 trixie
RUN echo "deb https://mirrors.aliyun.com/debian/ trixie main non-free contrib" > /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian-security trixie-security main" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian/ trixie-updates main non-free contrib" >> /etc/apt/sources.list
# --------------------------------------------------------

# 2. 工作目录
WORKDIR /app

# 3. 环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 4. 安装系统依赖，包括 postgresql-client
# 现在这个命令会从阿里云的镜像源下载，速度会非常快
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 4. 安装 uv
RUN pip install uv

# 5. 复制依赖文件
COPY requirements.in requirements.txt /app/

# 6. 安装 Python 依赖
RUN uv pip sync --system requirements.txt

# 7. 复制应用代码和脚本
COPY ./app /app/app
COPY ./alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY ./entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# 8. 暴露端口
EXPOSE 8000

# 9. 定义容器的入口点
ENTRYPOINT ["/app/entrypoint.sh"]