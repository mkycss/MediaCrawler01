# -*- coding: utf-8 -*-
"""
健康检查服务。

设计目标：
1. 把健康检查逻辑从 API 入口中拆出来，代码更清晰；
2. 区分 liveness（进程活着）和 readiness（服务可用）；
3. 返回足够具体的信息，方便你排查到底是哪一项没准备好。
"""

import os
from typing import Any, Dict

from sqlalchemy import text

import config
from database.db_session import get_async_engine
from tools import utils


class HealthService:
    """提供轻量健康检查能力。"""

    def _check_browser_data_root(self) -> Dict[str, Any]:
        """
        检查浏览器数据目录是否存在且可写。

        这是登录态持久化是否可靠的基础条件之一。
        """
        target_dir = config.BROWSER_DATA_ROOT
        try:
            os.makedirs(target_dir, exist_ok=True)
            test_file = os.path.join(target_dir, ".healthcheck.tmp")
            with open(test_file, "w", encoding="utf-8") as file:
                file.write("ok")
            os.remove(test_file)
            return {
                "status": "ok",
                "path": target_dir,
                "writable": True,
            }
        except OSError as exc:
            return {
                "status": "error",
                "path": target_dir,
                "writable": False,
                "message": str(exc),
            }

    def _check_cookie_config(self) -> Dict[str, Any]:
        """
        检查 Cookie 配置是否满足当前运行方式。

        注意：
        - 这里不做“知乎网络校验”，那属于登录状态校验接口的职责；
        - 这里只判断配置层面是否合理、关键字段是否存在。
        """
        result = {
            "status": "ok",
            "platform": config.PLATFORM,
            "login_type": config.LOGIN_TYPE,
            "cookie_source": config.COOKIE_SOURCE,
            "configured": bool(config.COOKIES),
        }

        if config.LOGIN_TYPE != "cookie":
            result["message"] = "当前不是 cookie 登录模式，无需检查 Cookie 配置"
            return result

        if not config.COOKIES:
            result["status"] = "error"
            result["message"] = "当前启用了 cookie 登录，但未配置 Cookie；如为首次部署，请先准备 Cookie 文件"
            return result

        # 知乎平台这里额外检查关键 Cookie 字段，避免看似有 Cookie 但实际不完整。
        if config.PLATFORM == "zhihu":
            cookie_dict = utils.convert_str_cookie_to_dict(config.COOKIES)
            missing_keys = [key for key in ["d_c0", "z_c0"] if not cookie_dict.get(key)]
            if missing_keys:
                result["status"] = "error"
                result["message"] = f"知乎 Cookie 缺少关键字段: {', '.join(missing_keys)}"
                return result

        result["message"] = "Cookie 配置存在且格式基础检查通过"
        return result

    async def _check_database(self) -> Dict[str, Any]:
        """
        检查数据库连通性。

        这里使用最轻量的 `SELECT 1`，避免健康检查本身带来过多负担。
        """
        db_type = config.SAVE_DATA_OPTION
        if db_type in ["json", "jsonl", "csv"]:
            return {
                "status": "ok",
                "db_type": db_type,
                "message": "当前为文件存储模式，无需数据库健康检查",
            }

        try:
            engine = get_async_engine(db_type)
            if engine is None:
                return {
                    "status": "error",
                    "db_type": db_type,
                    "message": "数据库引擎未初始化",
                }

            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

            return {
                "status": "ok",
                "db_type": db_type,
                "message": "数据库连接正常",
            }
        except Exception as exc:
            return {
                "status": "error",
                "db_type": db_type,
                "message": f"数据库连接失败: {exc}",
            }

    async def get_liveness(self) -> Dict[str, Any]:
        """存活检查：只说明 API 服务进程还活着。"""
        return {
            "status": "ok",
            "service": "mediacrawler-api",
        }

    async def get_readiness(self) -> Dict[str, Any]:
        """
        就绪检查：判断服务当前是否具备对外提供能力。

        目前聚焦 3 个核心条件：
        - 数据库可连接
        - 浏览器数据目录可写
        - Cookie 配置符合当前运行模式
        """
        db_check = await self._check_database()
        browser_check = self._check_browser_data_root()
        cookie_check = self._check_cookie_config()

        checks = {
            "database": db_check,
            "browser_data": browser_check,
            "cookie": cookie_check,
        }

        overall_status = "ok"
        failed_items = []
        for name, item in checks.items():
            if item.get("status") != "ok":
                overall_status = "error"
                failed_items.append(name)

        result = {
            "status": overall_status,
            "service": "mediacrawler-api",
            "checks": checks,
        }
        if failed_items:
            result["message"] = f"以下检查未通过: {', '.join(failed_items)}"
        else:
            result["message"] = "所有关键依赖检查通过"
        return result

    async def get_health_summary(self) -> Dict[str, Any]:
        """
        聚合健康摘要，方便前端和人工排查一次性看到所有关键信息。
        """
        liveness = await self.get_liveness()
        readiness = await self.get_readiness()
        return {
            "status": readiness["status"],
            "liveness": liveness,
            "readiness": readiness,
            "browser_data_root": config.BROWSER_DATA_ROOT,
            "save_login_state": config.SAVE_LOGIN_STATE,
            "cookie_source": config.COOKIE_SOURCE,
            "cookie_configured": bool(config.COOKIES),
        }


health_service = HealthService()
