# -*- coding: utf-8 -*-
"""
知乎登录态校验服务。

这个文件只做两件事：
1. 读取当前配置好的 Cookie；
2. 使用知乎现有的 API client 做一次轻量的登录态校验。

之所以单独抽成 service，是为了让：
- FastAPI 接口可以复用；
- 启动时校验也可以复用；
- 后续如果要扩展到别的平台，也有统一落点。
"""

from typing import Any, Dict, Optional

import config
from constant import zhihu as zhihu_constant
from media_platform.zhihu.client import ZhiHuClient
from tools import utils


class LoginService:
    """登录相关的轻量服务。"""

    def _build_zhihu_client(self, cookie_str: str) -> ZhiHuClient:
        """
        根据当前 Cookie 构造一个知乎 API client。

        这里不需要真的打开浏览器页面，
        因为登录态校验只调用知乎的当前用户接口。
        """
        cookie_dict = utils.convert_str_cookie_to_dict(cookie_str)
        return ZhiHuClient(
            proxy=None,
            headers={
                "accept": "*/*",
                "accept-language": "zh-CN,zh;q=0.9",
                "cookie": cookie_str,
                "priority": "u=1, i",
                "referer": "https://www.zhihu.com/search?q=python&time_interval=a_year&type=content",
                "user-agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "x-api-version": "3.0.91",
                "x-app-za": "OS=Web",
                "x-requested-with": "fetch",
                "x-zse-93": "101_3_3.0",
            },
            # 这里传 None 即可，pong() 校验路径不会用到 playwright_page。
            playwright_page=None,  # type: ignore[arg-type]
            cookie_dict=cookie_dict,
        )

    async def validate_zhihu_cookie(
        self,
        cookie_str: Optional[str] = None,
        cookie_source: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        使用知乎平台校验当前配置中的 Cookie 是否仍然有效。

        返回值里故意不包含原始 Cookie，
        只返回来源、状态和部分用户信息，避免敏感信息泄露。
        """
        actual_cookie_str = (cookie_str if cookie_str is not None else config.COOKIES).strip()
        actual_cookie_source = cookie_source or config.COOKIE_SOURCE

        if not actual_cookie_str:
            return {
                "success": False,
                "platform": "zhihu",
                "cookie_source": actual_cookie_source,
                "message": "未检测到 Cookie，请先配置 COOKIES 或 COOKIE_FILE",
            }

        cookie_dict = utils.convert_str_cookie_to_dict(actual_cookie_str)
        required_keys = ["d_c0", "z_c0"]
        missing_keys = [key for key in required_keys if not cookie_dict.get(key)]
        if missing_keys:
            return {
                "success": False,
                "platform": "zhihu",
                "cookie_source": actual_cookie_source,
                "message": f"Cookie 缺少关键字段: {', '.join(missing_keys)}",
            }

        try:
            zhihu_client = self._build_zhihu_client(actual_cookie_str)
            is_valid = await zhihu_client.pong()
            if not is_valid:
                return {
                    "success": False,
                    "platform": "zhihu",
                    "cookie_source": actual_cookie_source,
                    "message": "知乎 Cookie 已失效或当前网络环境无法通过校验",
                }

            user_info = await zhihu_client.get_current_user_info()
            return {
                "success": True,
                "platform": "zhihu",
                "cookie_source": actual_cookie_source,
                "message": "知乎 Cookie 校验成功",
                "user": {
                    "uid": user_info.get("uid"),
                    "name": user_info.get("name"),
                    "url": f"{zhihu_constant.ZHIHU_URL}/people/{user_info.get('url_token')}"
                    if user_info.get("url_token")
                    else None,
                },
            }
        except Exception as exc:
            return {
                "success": False,
                "platform": "zhihu",
                "cookie_source": actual_cookie_source,
                "message": "知乎 Cookie 校验异常",
                "error": str(exc),
            }


login_service = LoginService()
