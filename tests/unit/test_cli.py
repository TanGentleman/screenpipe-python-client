"""The CLI end to end against a fake server."""
import json
import socket

import pytest

from screenpipe_client.cli import main
from tests.fake_screenpipe import FakeScreenpipe


def run(capsys, *argv):
    code = main(list(argv))
    out = capsys.readouterr()
    return code, out.out, out.err


def test_health_check_is_the_default(capsys):
    with FakeScreenpipe({("GET", "/health"): (200, {"status": "healthy"})}) as fake:
        code, out, _ = run(capsys, "--port", str(fake.port))
    assert code == 0
    assert json.loads(out) == {"status": "healthy"}


def test_search_passes_filters_and_key(capsys):
    body = {"data": [], "pagination": {"limit": 5, "offset": 0, "total": 0}}
    with FakeScreenpipe({("GET", "/search"): (200, body)}) as fake:
        code, out, _ = run(capsys, "--port", str(fake.port), "--api-key", "k",
                           "search", "--query", "standup", "--limit", "5",
                           "--content-type", "audio")
    assert code == 0
    assert json.loads(out) == body
    request = fake.requests[-1]
    assert request["query"] == {"q": "standup", "limit": "5", "content_type": "audio"}
    assert request["headers"]["Authorization"] == "Bearer k"


def test_failure_exits_1(capsys):
    with FakeScreenpipe() as fake:
        code, out, err = run(capsys, "--port", str(fake.port), "list-pipes")
    assert code == 1
    assert out == ""
    assert f"localhost:{fake.port}" in err


def test_server_down_exits_1(capsys):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    code, out, err = run(capsys, "--host", "127.0.0.1", "--port", str(port))
    assert code == 1
    assert out == ""
    assert f"127.0.0.1:{port}" in err


def test_api_key_from_env(capsys, monkeypatch):
    monkeypatch.setenv("SCREENPIPE_API_KEY", "env-key")
    with FakeScreenpipe({("GET", "/health"): (200, {"status": "healthy"})}) as fake:
        code, _, _ = run(capsys, "--port", str(fake.port), "health-check")
    assert code == 0
    assert fake.requests[-1]["headers"]["Authorization"] == "Bearer env-key"


@pytest.mark.parametrize("argv, method, path, body", [
    (["get-pipe-info", "--pipe-id", "daily"], "GET", "/pipes/daily", None),
    (["install-pipe", "--source", "https://example.com/p.md"], "POST", "/pipes/install",
     {"source": "https://example.com/p.md"}),
    (["enable-pipe", "--pipe-id", "daily"], "POST", "/pipes/daily/enable", {"enabled": True}),
    (["disable-pipe", "--pipe-id", "daily"], "POST", "/pipes/daily/enable", {"enabled": False}),
    (["run-pipe", "--pipe-id", "daily"], "POST", "/pipes/daily/run", None),
    (["stop-pipe", "--pipe-id", "daily"], "POST", "/pipes/daily/stop", None),
    (["add-tags-to-content", "--content-type", "ocr", "--id", "7", "--tags", "a", "b"],
     "POST", "/tags/vision/7", {"tags": ["a", "b"]}),
    (["remove-tags-from-content", "--content-type", "audio", "--id", "7", "--tags", "a"],
     "DELETE", "/tags/audio/7", {"tags": ["a"]}),
    (["list-audio-devices"], "GET", "/audio/list", None),
    (["list-monitors"], "GET", "/vision/list", None),
])
def test_commands_map_to_routes(capsys, argv, method, path, body):
    with FakeScreenpipe({(method, path): (200, {"success": True})}) as fake:
        code, out, _ = run(capsys, "--port", str(fake.port), *argv)
    assert code == 0
    assert json.loads(out) == {"success": True}
    request = fake.requests[-1]
    assert (request["method"], request["path"], request["json"]) == (method, path, body)
