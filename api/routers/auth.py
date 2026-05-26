# -*- coding: utf-8 -*-
from fastapi import APIRouter

from ..services import login_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/zhihu/status")
async def validate_zhihu_login_status():
    """
    校验当前配置中的知乎 Cookie 是否有效。

    说明：
    - 这里只做“登录态是否可用”的轻量检测；
    - 不会返回原始 Cookie，避免敏感信息泄露；
    - 适合给前端、运维脚本或健康排查时调用。
    """
    return await login_service.validate_zhihu_cookie()
