#!/usr/bin/env bash
set -e

# 这个脚本只做一件事：等待 MySQL TCP 端口可以连通。
# 它不判断“业务表是否创建完成”，只负责确认数据库服务已经起来了。

MYSQL_HOST="${MYSQL_DB_HOST:-mysql}"
MYSQL_PORT="${MYSQL_DB_PORT:-3306}"
MYSQL_WAIT_TIMEOUT="${MYSQL_WAIT_TIMEOUT:-60}"

echo "[wait-for-mysql] 等待 MySQL 就绪: ${MYSQL_HOST}:${MYSQL_PORT}"

start_time=$(date +%s)

while true; do
  if python - <<PY
import socket
import sys

host = "${MYSQL_HOST}"
port = int("${MYSQL_PORT}")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2)

try:
    sock.connect((host, port))
except OSError:
    sys.exit(1)
finally:
    sock.close()
PY
  then
    echo "[wait-for-mysql] MySQL 已可连接"
    break
  fi

  now_time=$(date +%s)
  elapsed=$((now_time - start_time))

  if [ "${elapsed}" -ge "${MYSQL_WAIT_TIMEOUT}" ]; then
    echo "[wait-for-mysql] 等待超时，${MYSQL_WAIT_TIMEOUT} 秒内仍未连接到 MySQL"
    exit 1
  fi

  echo "[wait-for-mysql] MySQL 还未就绪，1 秒后重试..."
  sleep 1
done
