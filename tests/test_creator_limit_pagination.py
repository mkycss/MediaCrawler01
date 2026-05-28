# -*- coding: utf-8 -*-

import config
import pytest
from media_platform.douyin.client import DouYinClient
from media_platform.kuaishou.client import KuaiShouClient
from media_platform.weibo.client import WeiboClient
from media_platform.xhs.client import XiaoHongShuClient
from media_platform.zhihu.client import ZhiHuClient


@pytest.mark.asyncio
async def test_weibo_creator_limit_truncates_before_callback(monkeypatch):
    client = WeiboClient.__new__(WeiboClient)
    callback_batch_sizes = []
    requested_since_ids = []

    async def fake_sleep(_):
        return None

    async def fake_get_notes_by_creator(_creator_id, _container_id, since_id):
        requested_since_ids.append(since_id)
        if since_id == "":
            return {
                "cardlistInfo": {"since_id": "page-2", "total": 20},
                "cards": [
                    {"card_type": 9, "mblog": {"id": f"wb-1-{idx}"}}
                    for idx in range(10)
                ],
            }
        return {
            "cardlistInfo": {"since_id": "page-3", "total": 20},
            "cards": [
                {"card_type": 9, "mblog": {"id": f"wb-2-{idx}"}}
                for idx in range(10)
            ],
        }

    async def fake_callback(note_list):
        callback_batch_sizes.append(len(note_list))

    monkeypatch.setattr(config, "CREATOR_MAX_NOTES_COUNT", 15)
    monkeypatch.setattr("media_platform.weibo.client.asyncio.sleep", fake_sleep)
    client.get_notes_by_creator = fake_get_notes_by_creator

    notes = await client.get_all_notes_by_creator_id(
        creator_id="123",
        container_id="107603123",
        crawl_interval=0,
        callback=fake_callback,
    )

    assert requested_since_ids == ["", "page-2"]
    assert callback_batch_sizes == [10, 5]
    assert len(notes) == 15
    assert notes[-1]["mblog"]["id"] == "wb-2-4"


@pytest.mark.asyncio
async def test_douyin_creator_limit_truncates_before_callback(monkeypatch):
    client = DouYinClient.__new__(DouYinClient)
    callback_batch_sizes = []
    requested_cursors = []

    async def fake_get_user_aweme_posts(_sec_user_id, max_cursor):
        requested_cursors.append(max_cursor)
        if max_cursor == "":
            return {
                "has_more": 1,
                "max_cursor": "cursor-2",
                "aweme_list": [
                    {"aweme_id": f"dy-1-{idx}"}
                    for idx in range(10)
                ],
            }
        return {
            "has_more": 0,
            "max_cursor": "cursor-3",
            "aweme_list": [
                {"aweme_id": f"dy-2-{idx}"}
                for idx in range(10)
            ],
        }

    async def fake_callback(aweme_list):
        callback_batch_sizes.append(len(aweme_list))

    monkeypatch.setattr(config, "CREATOR_MAX_NOTES_COUNT", 15)
    client.get_user_aweme_posts = fake_get_user_aweme_posts

    aweme_list = await client.get_all_user_aweme_posts(
        sec_user_id="sec_user_id",
        callback=fake_callback,
    )

    assert requested_cursors == ["", "cursor-2"]
    assert callback_batch_sizes == [10, 5]
    assert len(aweme_list) == 15
    assert aweme_list[-1]["aweme_id"] == "dy-2-4"


@pytest.mark.asyncio
async def test_xhs_creator_limit_uses_creator_specific_config(monkeypatch):
    client = XiaoHongShuClient.__new__(XiaoHongShuClient)
    callback_batch_sizes = []
    requested_cursors = []

    async def fake_sleep(_):
        return None

    async def fake_get_notes_by_creator(_user_id, notes_cursor, xsec_token="", xsec_source="pc_feed"):
        requested_cursors.append(notes_cursor)
        _ = (xsec_token, xsec_source)
        if notes_cursor == "":
            return {
                "has_more": True,
                "cursor": "cursor-2",
                "notes": [
                    {"note_id": f"xhs-1-{idx}"}
                    for idx in range(10)
                ],
            }
        return {
            "has_more": False,
            "cursor": "cursor-3",
            "notes": [
                {"note_id": f"xhs-2-{idx}"}
                for idx in range(10)
            ],
        }

    async def fake_callback(note_list):
        callback_batch_sizes.append(len(note_list))

    monkeypatch.setattr(config, "CREATOR_MAX_NOTES_COUNT", 15)
    monkeypatch.setattr(config, "CRAWLER_MAX_NOTES_COUNT", 1)
    monkeypatch.setattr("media_platform.xhs.client.asyncio.sleep", fake_sleep)
    client.get_notes_by_creator = fake_get_notes_by_creator

    notes = await client.get_all_notes_by_creator(
        user_id="user-id",
        crawl_interval=0,
        callback=fake_callback,
    )

    assert requested_cursors == ["", "cursor-2"]
    assert callback_batch_sizes == [10, 5]
    assert len(notes) == 15
    assert notes[-1]["note_id"] == "xhs-2-4"


@pytest.mark.asyncio
async def test_kuaishou_creator_limit_truncates_before_callback(monkeypatch):
    client = KuaiShouClient.__new__(KuaiShouClient)
    callback_batch_sizes = []
    requested_pcursors = []

    async def fake_sleep(_):
        return None

    async def fake_get_video_by_creator(_user_id, pcursor):
        requested_pcursors.append(pcursor)
        if pcursor == "":
            return {
                "visionProfilePhotoList": {
                    "pcursor": "cursor-2",
                    "feeds": [
                        {"photo": {"id": f"ks-1-{idx}"}}
                        for idx in range(10)
                    ],
                }
            }
        return {
            "visionProfilePhotoList": {
                "pcursor": "no_more",
                "feeds": [
                    {"photo": {"id": f"ks-2-{idx}"}}
                    for idx in range(10)
                ],
            }
        }

    async def fake_callback(video_list):
        callback_batch_sizes.append(len(video_list))

    monkeypatch.setattr(config, "CREATOR_MAX_NOTES_COUNT", 15)
    monkeypatch.setattr("media_platform.kuaishou.client.asyncio.sleep", fake_sleep)
    client.get_video_by_creater = fake_get_video_by_creator

    videos = await client.get_all_videos_by_creator(
        user_id="user-id",
        crawl_interval=0,
        callback=fake_callback,
    )

    assert requested_pcursors == ["", "cursor-2"]
    assert callback_batch_sizes == [10, 5]
    assert len(videos) == 15
    assert videos[-1]["photo"]["id"] == "ks-2-4"


@pytest.mark.asyncio
async def test_zhihu_creator_limit_truncates_before_callback(monkeypatch):
    client = ZhiHuClient.__new__(ZhiHuClient)
    callback_batch_sizes = []
    requested_offsets = []

    async def fake_sleep(_):
        return None

    async def fake_get_creator_answers(_url_token, offset, _limit):
        requested_offsets.append(offset)
        if offset == 0:
            return {
                "paging": {"is_end": False},
                "data": [{"id": f"zh-1-{idx}"} for idx in range(10)],
            }
        return {
            "paging": {"is_end": True},
            "data": [{"id": f"zh-2-{idx}"} for idx in range(10)],
        }

    def fake_extract_content_list(data):
        return list(data)

    async def fake_callback(content_list):
        callback_batch_sizes.append(len(content_list))

    monkeypatch.setattr(config, "CREATOR_MAX_NOTES_COUNT", 15)
    monkeypatch.setattr("media_platform.zhihu.client.asyncio.sleep", fake_sleep)
    client.get_creator_answers = fake_get_creator_answers
    client._extractor = type("FakeExtractor", (), {"extract_content_list_from_creator": staticmethod(fake_extract_content_list)})()

    creator = type("FakeCreator", (), {"url_token": "zhihu-user"})()
    contents = await client.get_all_anwser_by_creator(
        creator=creator,
        crawl_interval=0,
        callback=fake_callback,
    )

    assert requested_offsets == [0, 20]
    assert callback_batch_sizes == [10, 5]
    assert len(contents) == 15
    assert contents[-1]["id"] == "zh-2-4"
