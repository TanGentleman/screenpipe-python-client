"""Pipe and auth calls against a fake server shaped like screenpipe 0.4.x."""
import pytest

from screenpipe_client import ScreenpipeClient
from tests.fake_screenpipe import FakeScreenpipe

PIPE = {"config": {"name": "daily"}, "is_running": False}


@pytest.fixture
def fake():
    with FakeScreenpipe({
        ("GET", "/health"): (200, {"status": "healthy"}),
        ("GET", "/pipes"): (200, {"data": [PIPE], "total": 1}),
        ("GET", "/pipes/daily"): (200, {"data": PIPE}),
        ("GET", "/pipes/missing"): (200, {"error": "pipe 'missing' not found"}),
        ("POST", "/pipes/install"): (200, {"success": True, "name": "daily"}),
        ("POST", "/pipes/daily/enable"): (200, {"success": True}),
        ("POST", "/pipes/daily/run"): (200, {"success": True}),
        ("POST", "/pipes/daily/stop"): (200, {"success": True, "status": "stopping"}),
        ("POST", "/pipes/daily/config"): (200, {"success": True}),
        ("DELETE", "/pipes/daily"): (200, {"success": True}),
    }) as server:
        yield server


@pytest.fixture
def client(fake, monkeypatch):
    monkeypatch.delenv("SCREENPIPE_API_KEY", raising=False)
    with ScreenpipeClient(host="127.0.0.1", port=fake.port) as c:
        yield c


def test_list_and_get_unwrap_data(client):
    assert client.list_pipes() == [PIPE]
    assert client.get_pipe_info("daily") == PIPE


def test_error_body_returns_none(client):
    assert client.get_pipe_info("missing") is None


def test_install_sends_source(client, fake):
    assert client.install_pipe("https://example.com/pipe") == {"success": True, "name": "daily"}
    assert fake.requests[-1]["json"] == {"source": "https://example.com/pipe"}
    assert client.download_pipe("x")["success"]


@pytest.mark.parametrize("enabled", [True, False])
def test_enable_pipe(client, fake, enabled):
    assert client.enable_pipe("daily", enabled=enabled) == {"success": True}
    assert fake.requests[-1]["json"] == {"enabled": enabled}


def test_run_stop_config_delete(client, fake):
    assert client.run_pipe("daily")["success"]
    assert client.stop_pipe("daily")["status"] == "stopping"
    assert client.update_pipe_configuration("daily", {"schedule": "daily"})["success"]
    assert fake.requests[-1]["json"] == {"schedule": "daily"}
    assert client.delete_pipe("daily")["success"]
    assert fake.requests[-1]["method"] == "DELETE"


def test_no_auth_header_by_default(client, fake):
    client.health_check()
    assert "Authorization" not in fake.requests[-1]["headers"]


def test_api_key_argument(fake):
    with ScreenpipeClient(host="127.0.0.1", port=fake.port, api_key="k1") as c:
        c.health_check()
    assert fake.requests[-1]["headers"]["Authorization"] == "Bearer k1"


def test_api_key_from_env(fake, monkeypatch):
    monkeypatch.setenv("SCREENPIPE_API_KEY", "k2")
    with ScreenpipeClient(host="127.0.0.1", port=fake.port) as c:
        c.list_pipes()
    assert fake.requests[-1]["headers"]["Authorization"] == "Bearer k2"


@pytest.mark.parametrize("content_type", ["input", "accessibility", "memory"])
def test_search_accepts_current_content_types(client, fake, content_type):
    client.search(content_type=content_type)
    assert fake.requests[-1]["query"]["content_type"] == content_type
