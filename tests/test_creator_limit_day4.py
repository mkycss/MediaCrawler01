# -*- coding: utf-8 -*-

import config
import pytest
from pydantic import ValidationError

from api.schemas import (
    CrawlerStartRequest,
    CrawlerTypeEnum,
    LoginTypeEnum,
    PlatformEnum,
    SaveDataOptionEnum,
)
from api.services import CrawlerManager
from cmd_arg import parse_cmd


@pytest.mark.asyncio
async def test_creator_cli_sets_creator_max_notes_count():
    result = await parse_cmd(
        [
            "--platform",
            "xhs",
            "--type",
            "creator",
            "--creator_id",
            "5eeb2d50000000000100b5c2",
            "--creator_max_notes_count",
            "12",
        ]
    )

    assert config.CREATOR_MAX_NOTES_COUNT == 12
    assert result.creator_max_notes_count == 12


def test_creator_request_rejects_negative_creator_max_notes_count():
    with pytest.raises(ValidationError):
        CrawlerStartRequest(
            platform=PlatformEnum.ZHIHU,
            login_type=LoginTypeEnum.COOKIE,
            crawler_type=CrawlerTypeEnum.CREATOR,
            creator_ids="zhihu-user",
            creator_max_notes_count=-1,
            save_option=SaveDataOptionEnum.JSONL,
        )


def test_build_command_includes_creator_limit_for_creator_mode():
    manager = CrawlerManager()
    request = CrawlerStartRequest(
        platform=PlatformEnum.ZHIHU,
        login_type=LoginTypeEnum.COOKIE,
        crawler_type=CrawlerTypeEnum.CREATOR,
        creator_ids="zhihu-user",
        creator_max_notes_count=12,
        save_option=SaveDataOptionEnum.JSONL,
        enable_comments=True,
        enable_sub_comments=False,
        headless=True,
    )

    cmd = manager._build_command(request)

    assert "--creator_id" in cmd
    assert "zhihu-user" in cmd
    assert "--creator_max_notes_count" in cmd
    assert "12" in cmd


def test_build_command_includes_creator_limit_without_creator_ids():
    manager = CrawlerManager()
    request = CrawlerStartRequest(
        platform=PlatformEnum.ZHIHU,
        login_type=LoginTypeEnum.COOKIE,
        crawler_type=CrawlerTypeEnum.CREATOR,
        creator_max_notes_count=3,
        save_option=SaveDataOptionEnum.JSONL,
        enable_comments=False,
        enable_sub_comments=False,
        headless=True,
    )

    cmd = manager._build_command(request)

    assert "--creator_id" not in cmd
    assert "--creator_max_notes_count" in cmd
    assert "3" in cmd


def test_build_command_omits_creator_limit_for_non_creator_mode():
    manager = CrawlerManager()
    request = CrawlerStartRequest(
        platform=PlatformEnum.ZHIHU,
        login_type=LoginTypeEnum.COOKIE,
        crawler_type=CrawlerTypeEnum.SEARCH,
        keywords="Python",
        creator_max_notes_count=12,
        save_option=SaveDataOptionEnum.JSONL,
        enable_comments=True,
        enable_sub_comments=False,
        headless=True,
    )

    cmd = manager._build_command(request)

    assert "--keywords" in cmd
    assert "Python" in cmd
    assert "--creator_max_notes_count" not in cmd
