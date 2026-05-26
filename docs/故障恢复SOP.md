# 故障恢复 SOP

本文档用于指导运维或开发在 `Docker + MySQL + Cookie 登录` 场景下快速排障。

建议搭配 [docker_mysql_deploy.md](file:///Users/monkey/Projects/demos/MediaCrawler01/docs/docker_mysql_deploy.md) 一起使用。

## 1. 常用排障入口

先按下面顺序排查：

1. 看容器状态
2. 看健康检查
3. 看应用日志
4. 看爬虫状态
5. 看知乎登录状态

对应命令：

```bash
docker compose ps
docker compose logs -f app
curl http://127.0.0.1:8080/api/health
curl http://127.0.0.1:8080/api/crawler/status
curl http://127.0.0.1:8080/api/auth/zhihu/status
```

## 2. 故障场景处理

## 2.1 app 容器一直不是 healthy

### 现象

- `docker compose ps` 中 `app` 一直是 `starting`
- 或健康检查失败

### 排查步骤

1. 查看 readiness：

```bash
curl -i http://127.0.0.1:8080/api/health/readiness
```

2. 查看聚合健康摘要：

```bash
curl http://127.0.0.1:8080/api/health
```

3. 查看应用日志：

```bash
docker compose logs --tail=100 app
```

### 常见原因

- MySQL 未准备好
- `LOGIN_TYPE=cookie` 但未配置 Cookie
- Cookie 文件不存在
- `/app/browser_data` 不可写

### 处理建议

- 确认 `.env` 配置是否正确
- 确认 `.secrets/zhihu.cookies` 是否存在
- 确认 `COOKIE_FILE=/run/secrets/zhihu.cookies`
- 确认 MySQL 正常启动

## 2.2 知乎 Cookie 失效

### 现象

- `/api/auth/zhihu/status` 返回 `success=false`
- `/api/crawler/start` 返回 `启动前登录校验失败`

### 处理步骤

1. 重新准备新的知乎 Cookie
2. 替换文件：

```bash
cp 新的cookie文件 .secrets/zhihu.cookies
```

3. 重建 app 容器：

```bash
docker compose up -d --force-recreate app
```

4. 再次验证：

```bash
curl http://127.0.0.1:8080/api/auth/zhihu/status
```

### 说明

不要把新的 Cookie 直接写进代码中。

## 2.3 启动爬虫时直接报 400

### 现象

`/api/crawler/start` 返回：

- `Crawler is already running`
- `启动前登录校验失败: 未检测到 Cookie`
- `启动前登录校验失败: 知乎 Cookie 已失效...`

### 排查步骤

查看状态：

```bash
curl http://127.0.0.1:8080/api/crawler/status
```

查看日志：

```bash
curl http://127.0.0.1:8080/api/crawler/logs?limit=50
```

### 处理建议

- 如果是正在运行：先停止现有爬虫
- 如果是 Cookie 问题：按 `2.2` 处理

## 2.4 MySQL 连接失败

### 现象

- `/api/health/readiness` 中 `database.status=error`
- 或启动日志中有数据库连接异常

### 排查步骤

1. 查看 MySQL 容器状态：

```bash
docker compose ps
```

2. 查看 MySQL 日志：

```bash
docker compose logs --tail=100 mysql
```

3. 检查 `.env`：

```env
MYSQL_DB_HOST=mysql
MYSQL_DB_PORT=3306
MYSQL_DB_USER=root
MYSQL_DB_PWD=123456
MYSQL_DB_NAME=media_crawler
```

### 处理建议

- 确认 `mysql` 服务已启动
- 确认密码与 `.env` 一致
- 必要时重启：

```bash
docker compose restart mysql app
```

## 2.5 浏览器登录态目录损坏

### 现象

- 登录状态异常
- 容器重启后无法继续复用登录态
- readiness 中 `browser_data.status=error`

### 处理步骤

1. 停止 app 容器：

```bash
docker compose stop app
```

2. 清理浏览器数据卷对应内容

如果你使用的是 Docker volume，可直接删除卷重新生成：

```bash
docker volume rm mediacrawler01_browser_data
```

如果是宿主机目录挂载，则删除对应目录内容即可。

3. 重新启动：

```bash
docker compose up -d app
```

4. 重新注入 Cookie 并验证

## 3. 标准恢复流程

当你不确定是哪一环出问题时，推荐按下面顺序恢复：

1. 确认 `.env` 正确
2. 确认 `.secrets/zhihu.cookies` 正确
3. 验证 MySQL 容器正常
4. 重建 app 容器
5. 检查 `/api/health`
6. 检查 `/api/auth/zhihu/status`
7. 再尝试启动爬虫

对应命令：

```bash
docker compose up -d --force-recreate app
curl http://127.0.0.1:8080/api/health
curl http://127.0.0.1:8080/api/auth/zhihu/status
```

## 4. 不建议的操作

以下操作不建议直接使用：

- 直接修改源码中的 Cookie
- 直接删除整个项目目录
- 在问题不明确时删除 MySQL 数据卷
- 在未备份情况下清空业务数据库

## 5. 建议保留的运维习惯

- 每次变更 Cookie 后都跑一次 `/api/auth/zhihu/status`
- 每次版本升级后都看一次 `/api/health/readiness`
- 定期备份 MySQL 数据卷
- 定期备份 `.env` 与 secrets 管理策略
