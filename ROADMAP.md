# Roadmap

A Python client and CLI for the [screenpipe](https://github.com/screenpipe/screenpipe) REST API
(port 3030): search your screen/audio history, check health, manage tags and pipes. For people who
script against a local screenpipe from Python.

## Upstream baseline (main `997496a`, checked 2026-11-07; still main on 2026-11-08)

- Installs: `uv pip install -e .` works on Python 3.10 and 3.12 (Poetry build backend).
- Tests: `pytest` stopped at collection (`ValueError: LLM_API_KEY not set` in `tests/unit/test_valves.py`).
  Without that file, 9 passed and 13 failed, all needing a live screenpipe, core server or LLM.
- CLI: `python cli/cli.py health-check` with screenpipe down logged an error and exited 0.
- `format_timestamp("2024-10-01T12:00:00Z")` raised `ValueError` (it appended a second `Z`).
- API drift vs screenpipe main (`crates/screenpipe-engine/src/server.rs`): pipes moved from
  `/pipes/list`, `/pipes/download`, `/pipes/enable` to `/pipes`, `/pipes/install`, `/pipes/{id}/enable`
  (and friends); list responses are now `{"data": [...]}`; non-health routes can require
  `Authorization: Bearer <key>`; search has new content types (`input`, `accessibility`, `memory`).
- Dead links (HTTP 404): `screenpipe-server/src/server.rs`, `content/docs/notes.md`,
  `examples/typescript/pipe-stream-ocr-text` (all in mediar-ai/screenpipe).
- Dependencies: `httpx` is imported by the client but not declared; the declared ones (`baml-py`,
  `openai`, `langchain-core`, `fastapi`) are Poetry caret pins from late 2024 for code the client
  does not use.
- Issue #48 ("Missing required field: user_message_content") is in the Open-WebUI pipe:
  `core_pipe.py` expects fields that only the filter function adds, so the pipe fails when the filter is not enabled first.

## Contract check (2026-11-07 against screenpipe main `32e9049`)

Compared every route, query parameter, request body, auth header and response field the client uses
with the Rust types in `crates/screenpipe-engine/src/` (`server.rs`, `routes/`, `pipes_api.rs`,
`video_utils.rs`) at `32e90499f96da33b687e6b3a6df9992251b12efa`. The checked-in `openapi.yaml`
lags the Rust source, so the Rust types win.

- Broken: `add_content` sent `data: {"frames": [...]}` / `data: {"transcription": {...}}`;
  screenpipe's untagged `ContentData` takes the list or the object itself (422 before, fixed).
- Broken: `update_speaker` sent `metadata` as a JSON object; `UpdateSpeakerRequest.metadata` is a
  string (422 before; a dict is now JSON-encoded, a string is passed through).
- Missing: search content type `parsed` (now accepted).
- Matches: all other routes, the search/unnamed-speaker query parameters the client sends, the
  `{"data": ...}` / `{"error": ...}` pipe envelopes, and `Authorization: Bearer <key>`.
  `/pipes` (no trailing slash) is right: axum 0.7 maps the nested `/` route to `/pipes`.
- Not wrapped (server has them, client doesn't): newer search filters such as `order`,
  `browser_url`, `focused`, `tags`, `fields`; pipe execution/log/history routes.
- `tests/contract/screenpipe_32e9049.json` records these shapes with the commit SHA;
  `tests/contract/test_server_contract.py` calls every client method against it.
  `SCREENPIPE_SRC=<checkout at 32e9049> uv run pytest tests/contract` re-checks the fixture
  (re-run for `-6`: 45 passed).

Live run: built `screenpipe` from `32e9049` on Ubuntu 22.04 (debug build; needed PipeWire 1.0
headers from the pipewire-debian PPA and a three-function `__isoc23_strto*` shim for the
prebuilt onnxruntime) and ran `screenpipe record --disable-audio --disable-vision` with
`SCREENPIPE_API_KEY` set. Against it: `health_check`, `search` (incl. `parsed`, filters,
`speaker_ids`), `add_content` with frames and with a transcription (both then found by `search`),
`add_tags_to_content`/`remove_tags_from_content` (vision and audio), `execute_raw_sql`,
`get_unnamed_speakers` and `list_pipes`/`get_pipe_info` worked and matched the fixture; requests
without the key got 403. The old `add_content` and dict-metadata bodies got 422
from the real server. `list_audio_devices` (500, no PulseAudio), `list_monitors` (404, no
display), `validate_media` (417 on a non-media file) and `update_speaker` (no speakers without
audio) only returned their headless errors. Pipe install/enable/run/stop/config/delete and
`merge_frames` were not run live.

## Stack

- `-1` done: dead links, timestamp fixes, offline tests with a fake server (live tests behind
  `SCREENPIPE_LIVE=1`), CLI exit code, GitHub Actions.
- `-2` done: current screenpipe API (pipe routes, bearer auth via `SCREENPIPE_API_KEY`, new
  content types) and the matching CLI commands, tested against a fake server.
- `-3` done: cut to client + CLI (-5,200 lines, 51 files); Poetry to uv with `uv.lock`; `httpx` is
  the only dependency; CI on 3.10 and 3.13.
- `-4` done: package renamed `src` -> `screenpipe_client`, `screenpipe-client` console script with
  `--host/--port/--api-key`, library no longer calls `logging.basicConfig`, PyPI metadata
  (`uv build` + `twine check` pass), new README.
- `-5` done: contract check against screenpipe `32e9049` (see above): fixed `add_content` and
  `update_speaker` bodies, accepted `content_type=parsed`, added the contract fixture and tests,
  ran the client against a real headless screenpipe.
- `-6` done: no new features. Pinned dev and build tools (pytest 9.2.0, ruff 0.17.4, hatchling
  1.33.0; httpx 0.28.1 was already the latest and stays `>=0.28.1,<1`); ruff config with
  `E,F,W,I,UP,B` and mechanical fixes (PEP 604/585 hints, import order, whitespace); offline tests
  for a down server, tags, unnamed speakers and every CLI command's route; CI on
  `actions/checkout` v7.0.1 and `astral-sh/setup-uv` v10.3.3 pinned by SHA, uv 0.13.7, Python
  3.10 and 3.15, running `uv sync --locked`, `uv run ruff check .` and `uv run pytest -q` as the
  README does; README rewritten (quickstart from a clone, commands, exit codes, env vars,
  boundaries). Not run against a live screenpipe.
- `-7` done: an unknown `--content-type` (`search`, `add-tags-to-content`,
  `remove-tags-from-content`) is an argparse usage error (`choices`, exit 2) instead of a
  `ValueError` traceback with exit 1; README exit-code table updated; tests for all three commands.
- `-8` done: README cut to 29 words; details moved to IMPLEMENTATION.md.

## Needs Tan

- Live coverage is partial (headless Linux, no audio or display; see the contract check). Pipe
  writes, `merge_frames` and `update_speaker` success paths are only checked against the
  fixture. `-6` was checked offline only (fake server, and the fixture against screenpipe's
  source with `SCREENPIPE_SRC`). Worth one run on a real desktop install.
- Re-check the fixture when screenpipe changes: bump the commit in
  `tests/contract/screenpipe_32e9049.json` (and its name) and run with `SCREENPIPE_SRC`.
- Breaking for SDK users: `-2` makes `run_pipe` run once (use `enable_pipe` to schedule); `-3`
  drops `SearchOutput`, `HealthCheck` and the Open-WebUI/BAML code; `-4` changes the import to
  `from screenpipe_client import ScreenpipeClient`; `-5` changes the `add_content` and
  `update_speaker` request bodies (the old ones were rejected by screenpipe).
- PyPI: the name `screenpipe-python-client` is free (pypi.org returned 404 on 2026-11-07 and
  2026-11-08). Not published; until it is, install from a clone (README quickstart).
- `.github/workflows/test.yml` only runs once applied upstream (kranti-sandbox ignores nested
  workflows). Its action SHAs and inputs were checked against GitHub and actionlint passes, but
  the workflow has not run; watch the first run, especially Python 3.15.
- `-7` changes the exit code for an unknown `--content-type` from 1 (traceback) to 2 (usage error).
- Cutting the Open-WebUI pipe (`-3`) drops the code issue #48 is about; close it with a note if you agree.
