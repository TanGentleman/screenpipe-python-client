"""ScreenpipeClient against a fake server; no screenpipe needed."""
import socket

import pytest

from screenpipe_client import ScreenpipeClient
from tests.fake_screenpipe import FakeScreenpipe

SEARCH_RESPONSE = {
    "data": [{"type": "OCR", "content": {"frame_id": 1, "text": "hello"}}],
    "pagination": {"limit": 1, "offset": 0, "total": 1},
}


@pytest.fixture
def fake():
    with FakeScreenpipe({
        ("GET", "/health"): (200, {"status": "healthy"}),
        ("GET", "/search"): (200, SEARCH_RESPONSE),
        ("GET", "/audio/list"): (200, [{"name": "mic", "is_default": True}]),
        ("POST", "/tags/vision/7"): (200, {"success": True}),
    }) as server:
        yield server


@pytest.fixture
def client(fake):
    with ScreenpipeClient(host="127.0.0.1", port=fake.port) as c:
        yield c


def test_health_check(client):
    assert client.health_check() == {"status": "healthy"}


def test_search_sends_only_set_params(client, fake):
    assert client.search(query="hello", limit=1, content_type="ocr") == SEARCH_RESPONSE
    assert fake.requests[-1]["query"] == {"q": "hello", "limit": "1", "content_type": "ocr"}


def test_search_joins_speaker_ids_and_flags_frames(client, fake):
    client.search(speaker_ids=[1, 2], include_frames=True)
    query = fake.requests[-1]["query"]
    assert query["speaker_ids"] == "1,2"
    assert query["include_frames"] == "true"


def test_search_rejects_unknown_content_type(client):
    with pytest.raises(ValueError):
        client.search(content_type="video")


def test_ocr_tags_map_to_vision(client, fake):
    assert client.add_tags_to_content("ocr", 7, ["a"]) == {"success": True}
    assert fake.requests[-1]["json"] == {"tags": ["a"]}


def test_http_error_returns_none(client):
    assert client.list_monitors() is None


def test_list_audio_devices(client):
    assert client.list_audio_devices() == [{"name": "mic", "is_default": True}]


def closed_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_server_down_returns_none():
    with ScreenpipeClient(host="127.0.0.1", port=closed_port()) as c:
        assert c.health_check() is None
        assert c.search(query="x") is None


def test_remove_tags_sends_delete_with_body(client, fake):
    client.remove_tags_from_content("audio", 7, ["a", "b"])
    request = fake.requests[-1]
    assert (request["method"], request["path"]) == ("DELETE", "/tags/audio/7")
    assert request["json"] == {"tags": ["a", "b"]}


def test_tags_reject_unknown_content_type(client, fake):
    with pytest.raises(ValueError):
        client.add_tags_to_content("input", 7, ["a"])
    assert fake.requests == []


def test_unnamed_speakers_sends_paging_and_ids(client, fake):
    client.get_unnamed_speakers(limit=3, speaker_ids=[4, 5])
    assert fake.requests[-1]["query"] == {"limit": "3", "offset": "0", "speaker_ids": "4,5"}
