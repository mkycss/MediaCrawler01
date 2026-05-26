#!/usr/bin/env bash
set -e

# 这个脚本负责容器默认启动流程：
# 1. 准备运行目录
# 2. 如果用户传了自定义命令，就执行自定义命令
# 3. 等待 MySQL 就绪
# 4. 执行幂等的建库建表初始化
# 5. 启动 FastAPI 服务

echo "[entrypoint] 正在准备运行目录..."
mkdir -p /app/data /app/browser_data /app/runtime

if [ "$#" -gt 0 ]; then
  echo "[entrypoint] 检测到自定义命令，直接执行: $*"
  exec "$@"
fi

echo "[entrypoint] 等待 MySQL 服务..."
/app/scripts/wait-for-mysql.sh

# 这里使用环境变量控制是否在容器启动时自动初始化数据库。
# Day 3 默认开启，后续如果你想手动控制，也可以把它改成 false。
if [ "${INIT_DB_ON_START:-true}" = "true" ]; then
  echo "[entrypoint] 开始执行 MySQL 建库建表..."
  uv run python main.py --init_db mysql
  echo "[entrypoint] MySQL 初始化完成"
else
  echo "[entrypoint] 已跳过 MySQL 初始化"
fi

echo "[entrypoint] 启动 MediaCrawler API 服务..."
exec uv run uvicorn api.main:app --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-8080}"
