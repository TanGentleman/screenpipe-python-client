"""The CLI end to end against a fake server."""
import json

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
