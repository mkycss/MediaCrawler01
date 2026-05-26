# Docker + MySQL 部署指南

本文档面向“`Docker Compose + MySQL + 容器内 Playwright + Cookie 登录`”的部署方式。

适用场景：

- 服务器无人值守长期运行
- 使用 `docker compose` 编排 `app + mysql`
- 使用浏览器持久化目录保存登录态
- 使用 MySQL 保存采集数据

## 1. 部署目标

当前项目已经具备以下能力：

- `app` 服务自动等待 MySQL
- 容器启动时自动建库建表
- 支持通过 `COOKIE_FILE` 注入 Cookie
- 支持知乎 Cookie 登录状态校验
- 支持 `liveness / readiness` 健康检查

推荐部署目录结构如下：

```text
MediaCrawler01/
├── .env
├── .secrets/
│   └── zhihu.cookies
├── docker-compose.yml
├── Dockerfile
└── docs/
```

## 2. 前置条件

部署前请先准备：

- 已安装 Docker
- 已安装 Docker Compose
- 服务器可访问 Docker Hub / Microsoft Playwright 镜像源
- 已准备 MySQL 持久化磁盘空间
- 已准备知乎 Cookie 文件

如果要抓取知乎或抖音，镜像内已经带有 Node.js 运行环境，不需要在宿主机单独安装。

## 3. 准备配置文件

先复制环境变量模板：

```bash
cp .env.docker.example .env
```

然后至少确认这些配置：

```env
APP_PORT=8080

MYSQL_ROOT_PASSWORD=123456
MYSQL_DB_HOST=mysql
MYSQL_DB_PORT=3306
MYSQL_DB_USER=root
MYSQL_DB_PWD=123456
MYSQL_DB_NAME=media_crawler

PLATFORM=zhihu
LOGIN_TYPE=cookie
CRAWLER_TYPE=search
SAVE_DATA_OPTION=db

HEADLESS=true
SAVE_LOGIN_STATE=true
ENABLE_CDP_MODE=false
BROWSER_DATA_ROOT=/app/browser_data

COOKIE_FILE=/run/secrets/zhihu.cookies
VALIDATE_ZHIHU_COOKIE_ON_START=false
```

说明：

- `PLATFORM=zhihu`：当前 Day 4/Day 5 登录校验以知乎为基准实现
- `LOGIN_TYPE=cookie`：无人值守场景推荐固定使用 cookie 登录
- `SAVE_DATA_OPTION=db`：表示写入 MySQL
- `COOKIE_FILE`：指向容器内的 Cookie 文件路径

## 4. 准备 Cookie 文件

先创建 secrets 目录：

```bash
mkdir -p .secrets
```

然后创建知乎 Cookie 文件：

```bash
touch .secrets/zhihu.cookies
```

把你的知乎 Cookie 原文粘贴进去，一行即可，例如：

```text
d_c0=xxx; z_c0=xxx; SESSIONID=xxx
```

注意：

- 不要把 Cookie 写进源码
- 不要把 Cookie 提交到 Git
- `.secrets/` 已加入 `.gitignore` 和 `.dockerignore`

## 5. 首次部署

执行以下命令：

```bash
docker compose up -d --build
```

这一步会完成：

- 拉起 MySQL 容器
- 拉起 app 容器
- app 等待 MySQL 可连接
- app 自动执行建库建表
- app 启动 FastAPI 服务

## 6. 部署后验证

### 6.1 查看容器状态

```bash
docker compose ps
```

### 6.2 查看应用日志

```bash
docker compose logs -f app
```

正常日志中应能看到类似内容：

```text
[entrypoint] 等待 MySQL 服务...
[wait-for-mysql] MySQL 已可连接
[entrypoint] 开始执行 MySQL 建库建表...
[entrypoint] MySQL 初始化完成
[entrypoint] 启动 MediaCrawler API 服务...
```

### 6.3 检查健康状态

存活检查：

```bash
curl http://127.0.0.1:8080/api/health/liveness
```

就绪检查：

```bash
curl -i http://127.0.0.1:8080/api/health/readiness
```

聚合健康摘要：

```bash
curl http://127.0.0.1:8080/api/health
```

### 6.4 检查知乎 Cookie

```bash
curl http://127.0.0.1:8080/api/auth/zhihu/status
```

如果返回 `success=true`，说明当前 Cookie 可用。

## 7. 启动与停止爬虫

### 7.1 启动爬虫

```bash
curl -X POST http://127.0.0.1:8080/api/crawler/start \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "zhihu",
    "login_type": "cookie",
    "crawler_type": "search",
    "keywords": "Python",
    "save_option": "db",
    "headless": true,
    "enable_comments": true,
    "enable_sub_comments": false
  }'
```

### 7.2 查看爬虫状态

```bash
curl http://127.0.0.1:8080/api/crawler/status
```

### 7.3 查看爬虫日志

```bash
curl http://127.0.0.1:8080/api/crawler/logs?limit=50
```

### 7.4 停止爬虫

```bash
curl -X POST http://127.0.0.1:8080/api/crawler/stop
```

## 8. 目录与卷说明

当前 `docker-compose.yml` 中主要用了 3 个卷：

- `mysql_data`：保存 MySQL 数据
- `app_data`：保存应用输出数据
- `browser_data`：保存 Playwright 浏览器登录态

同时还有 1 个本地只读挂载目录：

- `.secrets -> /run/secrets`

用途如下：

- `.secrets/zhihu.cookies`：保存知乎 Cookie 文件
- `/app/browser_data`：保存浏览器持久化上下文

## 9. 常见部署建议

### 9.1 生产建议开启启动时登录校验

如果你希望“Cookie 失效时容器直接启动失败”，可设置：

```env
VALIDATE_ZHIHU_COOKIE_ON_START=true
```

这样无人值守环境更容易被监控系统及时发现异常。

### 9.2 数据库备份

建议定期备份 MySQL：

- 备份 `mysql_data` 卷
- 或在容器内定期执行 `mysqldump`

### 9.3 Cookie 更新策略

建议按“文件替换 + 重启容器”的方式更新：

1. 替换 `.secrets/zhihu.cookies`
2. 执行 `docker compose up -d --force-recreate app`
3. 调用 `/api/auth/zhihu/status` 验证

## 10. 当前已知限制

- 当前登录状态校验的自动化基准是知乎平台
- 当前 Docker 健康检查使用 `/api/health/readiness`
- 如果配置了 `LOGIN_TYPE=cookie` 但没有 Cookie，`readiness` 会返回 `503`

这是有意设计的行为，表示：

- 进程活着，不等于服务已经可用
- 必须等数据库、浏览器目录、Cookie 配置都满足条件，才算真正“就绪”
