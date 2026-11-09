# screenpipe-python-client: implementation

## Requirements

- Python 3.10 or newer and [uv](https://docs.astral.sh/uv/) (CI: uv 0.13.7). One runtime
  dependency: `httpx` (0.28.1 in `uv.lock`, `httpx>=0.28.1,<1` for installs).
- A running [screenpipe](https://github.com/screenpipe/screenpipe), by default on
  `localhost:3030`. screenpipe `record` has `--api-auth` on by default: a headless screenpipe built
  from `32e9049` answered every route except `/health` with 403 when the key was missing, including
  on localhost, so set `SCREENPIPE_API_KEY`.
- The request and response shapes come from screenpipe commit `32e9049`
  (`tests/contract/screenpipe_32e9049.json`). Newer screenpipe releases may differ.

To install into another environment, run `pip install .` from the clone. That installs the
`screenpipe_client` package and the `screenpipe-client` command.

## Usage

```sh
export SCREENPIPE_API_KEY="$(screenpipe auth token)"
uv run screenpipe-client search --query standup --content-type audio --limit 5
```

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

| Exit code | Meaning |
| --- | --- |
| 0 | screenpipe answered; its JSON is on stdout |
| 1 | request failed (connection refused, HTTP error, or a pipe `error` body); the reason is on stderr |
| 2 | bad usage (argparse), including an unknown `--content-type` |

| Variable | Default | Purpose |
| --- | --- | --- |
| `SCREENPIPE_API_KEY` | none | Sent as `Authorization: Bearer <key>`. `--api-key` / `api_key=` override it. |
| `SCREENPIPE_SRC` | none | Tests only: a screenpipe checkout at `32e9049` to re-check the contract fixture. |

### Library

```python
from screenpipe_client import ScreenpipeClient

with ScreenpipeClient() as client:
    results = client.search(query="standup", content_type="audio", limit=5)
    for hit in results["data"]:
        print(hit["type"], hit["content"]["timestamp"], hit["content"]["text"])
```

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

## How it works

`screenpipe_client/client.py` holds `ScreenpipeClient`, one method per screenpipe route over an
`httpx` client to `http://<host>:<port>`, adding the bearer header when a key is set.
`screenpipe_client/cli.py` maps each subcommand to a client method with argparse and prints the
JSON. `screenpipe_client/time_utils.py` builds timestamps for search ranges.

## Tests

```sh
uv sync --locked
uv run ruff check .
uv run pytest -q
```

CI (`.github/workflows/test.yml`) runs these on Python 3.10 and 3.15. The tests use an in-process
fake server (`tests/fake_screenpipe.py`) on `127.0.0.1` and need no screenpipe and no network after
`uv sync`. `tests/contract/test_server_contract.py` checks every client method against the
fixture. To re-check the fixture against screenpipe's source:

```sh
GIT_LFS_SKIP_SMUDGE=1 git clone --filter=blob:none https://github.com/screenpipe/screenpipe /path/to/screenpipe
GIT_LFS_SKIP_SMUDGE=1 git -C /path/to/screenpipe checkout 32e90499f96da33b687e6b3a6df9992251b12efa
SCREENPIPE_SRC=/path/to/screenpipe uv run pytest -q tests/contract
```

Dev and build pins: pytest 9.2.0, ruff 0.17.4, hatchling 1.33.0.

## Limits

- Network: the client talks only to `http://<host>:<port>` (plain HTTP). It sends no telemetry and
  makes no other requests. `install_pipe` asks screenpipe to fetch the source; the client does not
  download it.
- Credentials: the only one is the screenpipe API key, sent as a bearer header. Over plain HTTP,
  use it only with a local screenpipe.
- `execute_raw_sql` sends your SQL as is to screenpipe's `POST /raw_sql`.
- Not wrapped: newer search filters such as `order`, `browser_url`, `focused`, `tags`, `fields`,
  and pipe execution, log and history routes. Live coverage is in [ROADMAP.md](ROADMAP.md).
