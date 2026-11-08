# screenpipe-python-client

A Python client and CLI for the local REST API of
[screenpipe](https://github.com/screenpipe/screenpipe), the open-source screen and audio recorder.
Search what it captured, check its health, and manage tags and pipes. One runtime dependency:
`httpx`.

## Quick start

```sh
git clone https://github.com/TanGentleman/screenpipe-python-client
cd screenpipe-python-client
uv sync --locked
uv run screenpipe-client --help
```

Everything below `--help` needs a running screenpipe, by default on `localhost:3030`:

```sh
export SCREENPIPE_API_KEY="$(screenpipe auth token)"
uv run screenpipe-client health-check
uv run screenpipe-client search --query standup --content-type audio --limit 5
```

```python
from screenpipe_client import ScreenpipeClient

with ScreenpipeClient() as client:
    results = client.search(query="standup", content_type="audio", limit=5)
    for hit in results["data"]:
        print(hit["type"], hit["content"]["timestamp"], hit["content"]["text"])
```

To install into another environment instead, run `pip install .` from the clone. That installs the
`screenpipe_client` package and the `screenpipe-client` command.

## Commands

```
screenpipe-client [--host HOST] [--port PORT] [--api-key KEY] <command> [options]

health-check                       # GET /health (the default command)
search [--query Q] [--content-type T] [--limit N] [--offset N]
       [--start-time ISO] [--end-time ISO] [--app-name A] [--window-name W]
       [--include-frames] [--min-length N] [--max-length N]
list-audio-devices                 # GET /audio/list
list-monitors                      # GET /vision/list
add-tags-to-content --content-type audio|vision|ocr --id N --tags T [T ...]
remove-tags-from-content --content-type audio|vision|ocr --id N --tags T [T ...]
list-pipes
get-pipe-info --pipe-id ID
install-pipe --source URL_OR_PATH
enable-pipe --pipe-id ID           # also disable-pipe, run-pipe, stop-pipe
```

`--content-type` for `search` is one of `all`, `ocr`, `audio`, `input`, `accessibility`, `memory`,
`parsed`. For tags, `ocr` is sent as `vision`. The CLI prints screenpipe's JSON response.

Exit codes:

| Code | Meaning |
| --- | --- |
| 0 | screenpipe answered; its JSON is on stdout |
| 1 | request failed (connection refused, HTTP error, or a pipe `error` body); the reason is on stderr |
| 2 | bad usage (argparse), including an unknown `--content-type` |

Environment variables:

| Variable | Effect |
| --- | --- |
| `SCREENPIPE_API_KEY` | Sent as `Authorization: Bearer <key>`. `--api-key` / `api_key=` override it. |
| `SCREENPIPE_SRC` | Tests only: a screenpipe checkout at `32e9049` to re-check the contract fixture. |

## Library

`ScreenpipeClient(port=3030, host="localhost", api_key=None)` is a context manager. Methods:
`health_check`, `search`, `list_audio_devices`, `list_monitors`, `add_tags_to_content`,
`remove_tags_from_content`, `list_pipes`, `get_pipe_info`, `install_pipe`, `enable_pipe`,
`run_pipe`, `stop_pipe`, `update_pipe_configuration`, `delete_pipe`, `add_content`,
`execute_raw_sql`, `merge_frames`, `validate_media`, `get_unnamed_speakers`, `update_speaker`.

- Each returns screenpipe's JSON, or `None` if the request failed; the error is logged through the
  `screenpipe_client.client` logger. The library does not configure logging.
- Pipe methods return the `data` field of screenpipe's `{"data": ...}` envelope, and `None` for an
  `{"error": ...}` body.
- `search` and the tag methods raise `ValueError` for an unknown content type before sending.
- `add_content(device, "frames", frames=[...])` or `add_content(device, "transcription",
  transcription={...})` sends the list or object as `content.data`.
- `update_speaker(id, name=..., metadata=...)` takes `metadata` as a dict (sent as a JSON string)
  or a string.
- `screenpipe_client.time_utils` has `format_timestamp` and `get_past_time` for search time ranges.

screenpipe's routes are in
[server.rs](https://github.com/screenpipe/screenpipe/blob/main/crates/screenpipe-engine/src/server.rs)
and its [API reference](https://docs.screenpi.pe/api-reference).

## Compatibility

- Python 3.10 or newer; CI runs 3.10 and 3.15.
- The request and response shapes come from screenpipe commit `32e9049`
  (`tests/contract/screenpipe_32e9049.json`). Newer screenpipe releases may differ.
- screenpipe `record` has `--api-auth` on by default. A headless screenpipe built from `32e9049`
  answered every route except `/health` with 403 when the key was missing, including on localhost,
  so set `SCREENPIPE_API_KEY`.

## Boundaries

- Network: the client talks only to `http://<host>:<port>` (plain HTTP, default
  `localhost:3030`). It sends no telemetry and makes no other requests. `install_pipe` asks
  screenpipe to fetch the source; the client does not download it.
- Credentials: the only one is the screenpipe API key, sent as a bearer header. Over plain HTTP,
  use it only with a local screenpipe.
- `execute_raw_sql` sends your SQL as is to screenpipe's `POST /raw_sql`.

## Develop

```sh
uv sync --locked
uv run ruff check .
uv run pytest -q
```

CI (`.github/workflows/test.yml`) runs these three commands. The tests use an in-process fake
server on `127.0.0.1` and need no screenpipe and no network after `uv sync`.
`tests/contract/test_server_contract.py` checks every client method against the fixture. To
re-check the fixture against screenpipe's source:

```sh
GIT_LFS_SKIP_SMUDGE=1 git clone --filter=blob:none https://github.com/screenpipe/screenpipe /path/to/screenpipe
GIT_LFS_SKIP_SMUDGE=1 git -C /path/to/screenpipe checkout 32e90499f96da33b687e6b3a6df9992251b12efa
SCREENPIPE_SRC=/path/to/screenpipe uv run pytest -q tests/contract
```

Pinned versions: uv 0.13.7 (CI), pytest 9.2.0, ruff 0.17.4, hatchling 1.33.0, httpx 0.28.1 in
`uv.lock` (`httpx>=0.28.1,<1` for installs).

## License

MIT
