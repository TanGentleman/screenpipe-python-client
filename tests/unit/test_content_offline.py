"""add_content and speaker calls against a fake server."""
import json

import pytest

from screenpipe_client import ScreenpipeClient
from tests.fake_screenpipe import FakeScreenpipe


@pytest.fixture
def fake():
    with FakeScreenpipe({
        ("POST", "/add"): (200, {"success": True, "message": None}),
        ("POST", "/speakers/update"): (200, {"id": 3, "name": "Ada", "metadata": "{}"}),
    }) as server:
        yield server


@pytest.fixture
def client(fake, monkeypatch):
    monkeypatch.delenv("SCREENPIPE_API_KEY", raising=False)
    with ScreenpipeClient(host="127.0.0.1", port=fake.port) as c:
        yield c


def test_add_frames_sends_the_list_as_data(client, fake):
    frames = [{"file_path": "/tmp/a.png", "app_name": "term"}]
    assert client.add_content("cam", "frames", frames=frames)["success"]
    assert fake.requests[-1]["json"] == {
        "device_name": "cam",
        "content": {"content_type": "frames", "data": frames},
    }


def test_add_transcription_sends_the_object_as_data(client, fake):
    transcription = {"transcription": "hi", "transcription_engine": "whisper"}
    client.add_content("mic", "transcription", transcription=transcription)
    assert fake.requests[-1]["json"]["content"] == {
        "content_type": "transcription", "data": transcription}


def test_add_content_needs_matching_payload(client):
    with pytest.raises(ValueError):
        client.add_content("mic", "transcription", frames=[{"file_path": "x"}])
    with pytest.raises(ValueError):
        client.add_content("cam", "frames", transcription={"transcription": "x"})


def test_update_speaker_sends_metadata_as_json_string(client, fake):
    assert client.update_speaker(3, name="Ada", metadata={"role": "pm"})["name"] == "Ada"
    body = fake.requests[-1]["json"]
    assert body["id"] == 3 and body["name"] == "Ada"
    assert isinstance(body["metadata"], str)
    assert json.loads(body["metadata"]) == {"role": "pm"}


def test_update_speaker_passes_string_metadata_through(client, fake):
    client.update_speaker(3, metadata='{"role": "pm"}')
    assert fake.requests[-1]["json"] == {"id": 3, "metadata": '{"role": "pm"}'}
