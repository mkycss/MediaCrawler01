# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/config/base_config.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

import os


def _get_env_str(name: str, default: str) -> str:
    """读取字符串环境变量，不存在时返回默认值。"""
    return os.getenv(name, default)


def _get_env_int(name: str, default: int) -> int:
    """读取整数环境变量，格式错误时回退到默认值。"""
    raw_value = os.getenv(name)
    if raw_value in (None, ""):
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def _get_env_bool(name: str, default: bool) -> bool:
    """读取布尔环境变量，支持 true/false/1/0/yes/no。"""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _load_cookie_config() -> tuple[str, str]:
    """
    统一读取 Cookie 配置。

    读取优先级：
    1. COOKIES 环境变量
    2. COOKIE_FILE 指向的文件
    3. 都没有时返回空字符串

    返回值：
    - 第一个值：实际 Cookie 字符串
    - 第二个值：Cookie 来源，便于健康检查和调试
    """
    cookie_from_env = os.getenv("COOKIES", "").strip()
    if cookie_from_env:
        return cookie_from_env, "env"

    cookie_file = os.getenv("COOKIE_FILE", "").strip()
    if not cookie_file:
        return "", "none"

    try:
        with open(cookie_file, "r", encoding="utf-8") as file:
            cookie_from_file = file.read().strip()
    except OSError:
        return "", "file_missing"

    if cookie_from_file:
        return cookie_from_file, "file"
    return "", "file_empty"


# Basic configuration
# 这里统一采用“环境变量优先，源码默认值兜底”的方式。
# 这样本地开发可以直接跑，容器部署时也不用进源码改常量。
APP_HOST = _get_env_str("APP_HOST", "0.0.0.0")
APP_PORT = _get_env_int("APP_PORT", 8080)
PLATFORM = _get_env_str("PLATFORM", "xhs")  # Platform, xhs | dy | ks | bili | wb | tieba | zhihu

# 是否使用海外版小红书 (rednote.com)
# 开启后 API 走 webapi.rednote.com，cookie 域使用 .rednote.com
XHS_INTERNATIONAL = _get_env_bool("XHS_INTERNATIONAL", False)

KEYWORDS = _get_env_str("KEYWORDS", "编程副业,编程兼职")  # Keyword search configuration, separated by English commas
LOGIN_TYPE = _get_env_str("LOGIN_TYPE", "qrcode")  # qrcode or phone or cookie
COOKIE_FILE = _get_env_str("COOKIE_FILE", "")
COOKIES, COOKIE_SOURCE = _load_cookie_config()
CRAWLER_TYPE = _get_env_str(
    "CRAWLER_TYPE",
    "search",  # Crawling type, search (keyword search) | detail (post details) | creator (creator homepage data)
)
VALIDATE_ZHIHU_COOKIE_ON_START = _get_env_bool("VALIDATE_ZHIHU_COOKIE_ON_START", False)
# Whether to enable IP proxy
ENABLE_IP_PROXY = _get_env_bool("ENABLE_IP_PROXY", False)

# Number of proxy IP pools
IP_PROXY_POOL_COUNT = _get_env_int("IP_PROXY_POOL_COUNT", 2)

# Proxy IP provider name
IP_PROXY_PROVIDER_NAME = _get_env_str("IP_PROXY_PROVIDER_NAME", "kuaidaili")  # kuaidaili | wandouhttp

# Setting to True will not open the browser (headless browser)
# Setting False will open a browser
# If Xiaohongshu keeps scanning the code to log in but fails, open the browser and manually pass the sliding verification code.
# If Douyin keeps prompting failure, open the browser and see if mobile phone number verification appears after scanning the QR code to log in. If it does, manually go through it and try again.
HEADLESS = _get_env_bool("HEADLESS", False)

# Whether to save login status
SAVE_LOGIN_STATE = _get_env_bool("SAVE_LOGIN_STATE", True)

# ==================== CDP (Chrome DevTools Protocol) 配置 ====================
# 是否启用 CDP 模式 - 使用用户本地的 Chrome/Edge 浏览器进行爬取，具有更好的反检测能力
# 开启后，会自动检测并启动用户的 Chrome/Edge 浏览器，通过 CDP 协议进行控制
# 该方式使用真实浏览器环境，包括用户的扩展、Cookie 和设置，大幅降低被风控检测的风险
ENABLE_CDP_MODE = _get_env_bool("ENABLE_CDP_MODE", True)

# CDP 调试端口，用于与浏览器通信
# 如果端口被占用，系统会自动尝试下一个可用端口
CDP_DEBUG_PORT = _get_env_int("CDP_DEBUG_PORT", 9222)

# 自定义浏览器路径（可选）
# 如果为空，系统会自动检测 Chrome/Edge 的安装路径
# Windows 示例: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
# macOS 示例: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CUSTOM_BROWSER_PATH = _get_env_str("CUSTOM_BROWSER_PATH", "")

# 是否在 CDP 模式下启用无头模式
# 注意：即使设置为 True，某些反检测功能在无头模式下可能无法正常工作
CDP_HEADLESS = _get_env_bool("CDP_HEADLESS", False)

# 浏览器启动超时时间（秒）
BROWSER_LAUNCH_TIMEOUT = _get_env_int("BROWSER_LAUNCH_TIMEOUT", 60)

# 是否连接用户已打开的浏览器，而不是启动新的浏览器
# 开启后，程序会连接一个已经启用了远程调试的浏览器
# 用户需要在 Chrome 中开启远程调试：chrome://inspect/#remote-debugging
# 或者使用命令行参数启动 Chrome：--remote-debugging-port=9222
# 这种方式反检测效果最好，因为直接使用用户真实浏览器的所有 Cookie、扩展和浏览历史
CDP_CONNECT_EXISTING = _get_env_bool("CDP_CONNECT_EXISTING", True)

# 程序结束时是否自动关闭浏览器
# 设置为 False 可以保持浏览器运行，方便调试
AUTO_CLOSE_BROWSER = _get_env_bool("AUTO_CLOSE_BROWSER", True)

# Data saving type option configuration, supports: csv, db, json, jsonl, sqlite, excel, postgres. It is best to save to DB, with deduplication function.
SAVE_DATA_OPTION = _get_env_str("SAVE_DATA_OPTION", "jsonl")  # csv or db or json or jsonl or sqlite or excel or postgres

# Data saving path, if not specified by default, it will be saved to the data folder.
SAVE_DATA_PATH = _get_env_str("SAVE_DATA_PATH", "")

# Browser file configuration cached by the user's browser
USER_DATA_DIR = _get_env_str("USER_DATA_DIR", "%s_user_data_dir")  # %s will be replaced by platform name

# 这里先把浏览器数据根目录也环境变量化，后续 Day 4 做登录态持久化时会直接复用。
BROWSER_DATA_ROOT = _get_env_str("BROWSER_DATA_ROOT", os.path.join(os.getcwd(), "browser_data"))

# The number of pages to start crawling starts from the first page by default
START_PAGE = _get_env_int("START_PAGE", 1)

# Control the number of crawled videos/posts
CRAWLER_MAX_NOTES_COUNT = _get_env_int("CRAWLER_MAX_NOTES_COUNT", 15)

# Controlling the number of concurrent crawlers
MAX_CONCURRENCY_NUM = _get_env_int("MAX_CONCURRENCY_NUM", 1)

# Whether to enable crawling media mode (including image or video resources), crawling media is not enabled by default
ENABLE_GET_MEIDAS = _get_env_bool("ENABLE_GET_MEIDAS", False)

# Whether to enable comment crawling mode. Comment crawling is enabled by default.
ENABLE_GET_COMMENTS = _get_env_bool("ENABLE_GET_COMMENTS", True)

# Control the number of crawled first-level comments (single video/post)
CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES = _get_env_int("CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES", 10)

# Whether to enable the mode of crawling second-level comments. By default, crawling of second-level comments is not enabled.
# If the old version of the project uses db, you need to refer to schema/tables.sql line 287 to add table fields.
ENABLE_GET_SUB_COMMENTS = _get_env_bool("ENABLE_GET_SUB_COMMENTS", False)

# word cloud related
# Whether to enable generating comment word clouds
ENABLE_GET_WORDCLOUD = _get_env_bool("ENABLE_GET_WORDCLOUD", False)
# Custom words and their groups
# Add rule: xx:yy where xx is a custom-added phrase, and yy is the group name to which the phrase xx is assigned.
CUSTOM_WORDS = {
    "零几": "年份",  # Recognize "zero points" as a whole
    "高频词": "专业术语",  # Example custom words
}

# Deactivate (disabled) word file path
STOP_WORDS_FILE = _get_env_str("STOP_WORDS_FILE", "./docs/hit_stopwords.txt")

# Chinese font file path
FONT_PATH = _get_env_str("FONT_PATH", "./docs/STZHONGS.TTF")

# Crawl interval
CRAWLER_MAX_SLEEP_SEC = _get_env_int("CRAWLER_MAX_SLEEP_SEC", 2)

# 是否禁用 SSL 证书验证。仅在使用企业代理、Burp Suite、mitmproxy 等会注入自签名证书的中间人代理时设为 True。
# 警告：禁用 SSL 验证将使所有流量暴露于中间人攻击风险，请勿在生产环境中开启。
DISABLE_SSL_VERIFY = _get_env_bool("DISABLE_SSL_VERIFY", False)

from .bilibili_config import *
from .xhs_config import *
from .dy_config import *
from .ks_config import *
from .weibo_config import *
from .tieba_config import *
from .zhihu_config import *
