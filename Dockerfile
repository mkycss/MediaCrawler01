FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

# 使用 /app 作为容器内工作目录，后续所有命令都在这里执行
WORKDIR /app

# 这些环境变量是容器运行时的通用默认值
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy \
    APP_HOST=0.0.0.0 \
    APP_PORT=8080

# 一些 Python 依赖在安装时会编译 C 扩展；知乎签名还依赖 nodejs 运行 execjs。
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv，用它来管理 Python 依赖
RUN pip install --no-cache-dir uv

# 先复制整个项目，Day 1 以“结构清晰、容易理解”为主
COPY . /app

# 安装项目依赖，并准备运行时目录
RUN uv sync --frozen \
    && chmod +x /app/scripts/entrypoint.sh \
    && chmod +x /app/scripts/wait-for-mysql.sh \
    && mkdir -p /app/data /app/browser_data /app/runtime

EXPOSE 8080

# 统一通过启动脚本进入应用，后续 Day 2/Day 3 可继续扩展
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
