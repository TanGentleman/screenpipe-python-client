"""Check every client call against screenpipe's server types.

The fixture is built by hand from the Rust request/response types of the
screenpipe commit it names. Set SCREENPIPE_SRC to a checkout of that commit
to re-check the fixture against the source.
"""
import json
import os
import re
import subprocess
from pathlib import Path

import pytest

from screenpipe_client import ScreenpipeClient
from tests.fake_screenpipe import FakeScreenpipe

FIXTURE = json.loads(
    (Path(__file__).parent / "screenpipe_32e9049.json").read_text())
ROUTES = FIXTURE["routes"]
COMMIT = FIXTURE["upstream"]["commit"]

JSON_TYPES = {
    "string": str, "integer": int, "number": (int, float), "boolean": bool,
    "object": dict, "array": list, "null": type(None),
}


def errors(value, schema, where="$"):
    """Problems with value against a small JSON Schema subset."""
    if "oneOf" in schema:
        if any(not errors(value, s, where) for s in schema["oneOf"]):
            return []
        return [f"{where}: matches no oneOf branch: {value!r}"]
    if "enum" in schema and value not in schema["enum"]:
        return [f"{where}: {value!r} not in {schema['enum']}"]
    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        ok = any(isinstance(value, JSON_TYPES[t])
                 and not (t in ("integer", "number") and isinstance(value, bool))
                 for t in types)
        if not ok:
            return [f"{where}: {value!r} is not {schema['type']}"]
    if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
        return [f"{where}: {value!r} does not match {schema['pattern']}"]
    found = []
    if isinstance(value, dict):
        props = schema.get("properties", {})
        found += [f"{where}: missing {k}" for k in schema.get("required", []) if k not in value]
        for key, item in value.items():
            if key in props:
                found += errors(item, props[key], f"{where}.{key}")
            elif schema.get("additionalProperties") is False:
                found.append(f"{where}: unknown field {key} (screenpipe ignores it)")
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            found += errors(item, schema["items"], f"{where}[{i}]")
    return found


def coerce_query(raw, schema):
    """Query strings arrive as text; parse the typed ones like serde does."""
    out = {}
    for key, text in raw.items():
        kind = schema.get("properties", {}).get(key, {}).get("type")
        if kind == "integer" and re.fullmatch(r"-?[0-9]+", text):
            out[key] = int(text)
        elif kind == "boolean" and text in ("true", "false"):
            out[key] = text == "true"
        else:
            out[key] = text
    return out


def route_for(method, path):
    for key, route in ROUTES.items():
        route_method, template = key.split(" ", 1)
        params = re.findall(r"{(\w+)}", template)
        pattern = re.sub(r"{\w+}", "([^/]+)", template)
        match = re.fullmatch(pattern, path)
        if route_method == method and match:
            values = dict(zip(params, match.groups()))
            for name, allowed in route.get("path_params", {}).items():
                assert values[name] in allowed, f"{key}: {name}={values[name]}"
            return key, route
    raise AssertionError(f"{method} {path} is not a screenpipe route at {COMMIT[:7]}")


def concrete(key):
    method, template = key.split(" ", 1)
    return method, template.replace("{content_type}", "vision").replace("{id}", "7")


CALLS = {
    "GET /health": lambda c: c.health_check(),
    "GET /search": lambda c: c.search(
        query="standup", content_type="audio", limit=5, offset=0,
        start_time="2026-11-06T00:00:00Z", end_time="2026-11-07T00:00:00Z",
        app_name="Zoom", window_name="standup", include_frames=True,
        min_length=1, max_length=500, speaker_ids=[3, 4]),
    "GET /audio/list": lambda c: c.list_audio_devices(),
    "GET /vision/list": lambda c: c.list_monitors(),
    "POST /tags/{content_type}/{id}": lambda c: c.add_tags_to_content("ocr", 7, ["work"]),
    "DELETE /tags/{content_type}/{id}": lambda c: c.remove_tags_from_content("ocr", 7, ["work"]),
    "GET /pipes": lambda c: c.list_pipes(),
    "GET /pipes/{id}": lambda c: c.get_pipe_info("7"),
    "POST /pipes/install": lambda c: c.install_pipe("https://example.com/pipe.md"),
    "POST /pipes/{id}/enable": lambda c: c.enable_pipe("7", False),
    "POST /pipes/{id}/run": lambda c: c.run_pipe("7"),
    "POST /pipes/{id}/stop": lambda c: c.stop_pipe("7"),
    "POST /pipes/{id}/config": lambda c: c.update_pipe_configuration("7", {"schedule": "every 2h"}),
    "DELETE /pipes/{id}": lambda c: c.delete_pipe("7"),
    "POST /add": lambda c: c.add_content(
        "monitor_1", "frames",
        frames=[{"file_path": "/tmp/a.png", "app_name": "Notes",
                 "ocr_results": [{"text": "hello", "focused": True}], "tags": ["x"]}]),
    "POST /raw_sql": lambda c: c.execute_raw_sql("SELECT 1"),
    "POST /experimental/frames/merge": lambda c: c.merge_frames(["/data/a.mp4", "/data/b.mp4"]),
    "GET /experimental/validate/media": lambda c: c.validate_media("/data/a.mp4"),
    "GET /speakers/unnamed": lambda c: c.get_unnamed_speakers(limit=5, offset=0, speaker_ids=[3]),
    "POST /speakers/update": lambda c: c.update_speaker(3, name="Ada", metadata={"role": "pm"}),
}

PIPE_ENVELOPE = {"GET /pipes", "GET /pipes/{id}"}


@pytest.fixture
def served():
    routes = {concrete(key): (200, route["example"]) for key, route in ROUTES.items()}
    with FakeScreenpipe(routes) as server:
        yield server


def test_fixture_records_upstream_commit():
    assert re.fullmatch(r"[0-9a-f]{40}", COMMIT)
    assert COMMIT.startswith("32e9049")


def test_every_route_in_the_fixture_is_called():
    assert set(CALLS) == set(ROUTES)


@pytest.mark.parametrize("key", sorted(ROUTES))
def test_examples_match_response_schema(key):
    assert errors(ROUTES[key]["example"], ROUTES[key]["response"]) == []


@pytest.mark.parametrize("key", sorted(CALLS))
def test_client_request_matches_server_types(key, served, monkeypatch):
    monkeypatch.delenv("SCREENPIPE_API_KEY", raising=False)
    with ScreenpipeClient(host="127.0.0.1", port=served.port, api_key="secret") as client:
        result = CALLS[key](client)

    request = served.requests[-1]
    matched, route = route_for(request["method"], request["path"])
    assert matched == key

    query_schema = route.get("query", {"type": "object", "properties": {},
                                       "additionalProperties": False})
    assert errors(coerce_query(request["query"], query_schema), query_schema) == []
    body_schema = route.get("body", {"type": "null"})
    assert errors(request["json"], body_schema) == []

    auth = FIXTURE["auth"]
    assert request["headers"][auth["header"]] == f"{auth['scheme']} secret"

    expected = route["example"]
    assert result == (expected["data"] if key in PIPE_ENVELOPE else expected)


def test_search_hit_examples_match_content_types():
    search = ROUTES["GET /search"]
    for hit in search["example"]["data"]:
        assert errors(hit["content"], search["content_by_type"][hit["type"]]) == []
        assert {"timestamp", "text"} <= set(hit["content"])


def test_old_add_content_shape_is_rejected_by_the_fixture():
    body = ROUTES["POST /add"]["body"]
    old = {"device_name": "m", "content": {"content_type": "frames",
                                          "data": {"frames": [{"file_path": "a"}]}}}
    assert errors(old, body)


@pytest.mark.skipif(not os.environ.get("SCREENPIPE_SRC"),
                    reason="set SCREENPIPE_SRC to a screenpipe checkout")
def test_fixture_matches_upstream_source():
    src = Path(os.environ["SCREENPIPE_SRC"])
    head = subprocess.run(["git", "-C", str(src), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    assert head == COMMIT
    server = (src / "crates/screenpipe-engine/src/server.rs").read_text()
    for key, route in ROUTES.items():
        _, template = key.split(" ", 1)
        axum_path = re.sub(r"{(\w+)}", r":\1", template)
        if axum_path.startswith("/pipes"):
            axum_path = axum_path[len("/pipes"):] or "/"
        assert f'"{axum_path}"' in server, f"{key} missing from server.rs"
        files = re.findall(r"crates/\S+\.rs", route["source"])
        text = "".join((src / f).read_text() for f in files)
        for part in ("query", "body"):
            for field in route.get(part, {}).get("properties", {}):
                assert re.search(rf"\b{field}\b", text), f"{key}: {field} not in {files}"
    for path in FIXTURE["auth"]["exempt_paths"]:
        assert f'path == "{path}"' in server
