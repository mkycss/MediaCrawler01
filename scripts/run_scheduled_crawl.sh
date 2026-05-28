#!/usr/bin/env bash
set -euo pipefail

# 这个脚本用于被 crontab 定时调用：
# 1. 读取当前爬虫状态
# 2. 如果已有任务在运行，则跳过本次触发
# 3. 否则调用现有 API 启动一次爬虫

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8080}"
STATUS_URL="${STATUS_URL:-${API_BASE_URL}/api/crawler/status}"
START_URL="${START_URL:-${API_BASE_URL}/api/crawler/start}"
PAYLOAD_FILE="${PAYLOAD_FILE:-${SCRIPT_DIR}/scheduled_crawl.payload.json}"
LOG_DIR="${LOG_DIR:-${PROJECT_ROOT}/runtime}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/scheduled_crawl.log}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
CURL_BIN="${CURL_BIN:-$(command -v curl)}"

mkdir -p "${LOG_DIR}"

timestamp() {
  date '+%Y-%m-%d %H:%M:%S'
}

log() {
  local message="$1"
  printf '[scheduled-crawl] %s %s\n' "$(timestamp)" "${message}" | tee -a "${LOG_FILE}"
}

require_command() {
  local cmd="$1"
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    log "缺少命令: ${cmd}"
    exit 1
  fi
}

require_file() {
  local file_path="$1"
  if [ ! -f "${file_path}" ]; then
    log "未找到请求体文件: ${file_path}"
    log "可先复制示例文件: ${SCRIPT_DIR}/scheduled_crawl.payload.example.json"
    exit 1
  fi
}

require_command "${CURL_BIN}"
require_command "${PYTHON_BIN}"
require_file "${PAYLOAD_FILE}"

if ! "${PYTHON_BIN}" - "${PAYLOAD_FILE}" >>"${LOG_FILE}" 2>&1 <<'PY'
import json
import sys

payload_path = sys.argv[1]
with open(payload_path, "r", encoding="utf-8") as f:
    json.load(f)
PY
then
  log "请求体 JSON 非法: ${PAYLOAD_FILE}"
  exit 1
fi

log "开始执行定时爬取，状态接口: ${STATUS_URL}"

status_response="$("${CURL_BIN}" -fsS "${STATUS_URL}")" || {
  log "读取状态失败，无法访问 API: ${STATUS_URL}"
  exit 1
}

current_status="$(printf '%s' "${status_response}" | "${PYTHON_BIN}" -c 'import json,sys; print(json.load(sys.stdin).get("status",""))')"

case "${current_status}" in
  running|stopping)
    log "当前爬虫状态为 ${current_status}，跳过本次触发"
    exit 0
    ;;
  idle|error)
    log "当前爬虫状态为 ${current_status}，准备触发启动"
    ;;
  *)
    log "未知爬虫状态: ${current_status}"
    log "状态响应: ${status_response}"
    exit 1
    ;;
esac

response_file="$(mktemp)"
trap 'rm -f "${response_file}"' EXIT

http_code="$("${CURL_BIN}" -sS -o "${response_file}" -w '%{http_code}' \
  -X POST "${START_URL}" \
  -H 'Content-Type: application/json' \
  --data @"${PAYLOAD_FILE}")"

response_body="$(cat "${response_file}")"

if [ "${http_code}" -ge 200 ] && [ "${http_code}" -lt 300 ]; then
  log "启动请求成功，HTTP ${http_code}"
  log "响应内容: ${response_body}"
  exit 0
fi

log "启动请求失败，HTTP ${http_code}"
log "响应内容: ${response_body}"
exit 1
