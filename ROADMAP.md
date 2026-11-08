# Roadmap

A Python client and CLI for the [screenpipe](https://github.com/mediar-ai/screenpipe) REST API
(port 3030): search your screen/audio history, check health, manage tags and pipes. For people who
script against a local screenpipe from Python.

## Status (checked 2026-11-07 against upstream main `997496a`)

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
- Dependencies: `httpx` is imported by the client but not declared. Caret pins hold everything at
  late-2024 majors: `baml-py` 0.68 (latest 0.226), `openai` 1.x (3.x), `langchain-core` 0.3 (1.x),
  `fastapi` 0.115 (0.162). Only `httpx` is needed for the client.
- Issue #48 ("Invalid Pipe Body") is in the Open-WebUI pipe: `core_pipe.py` expects fields that only
  the filter function adds, so the pipe fails when the filter is not enabled first.

## Signal vs noise

Keep: `src/core/screenpipe.py` (the client), `cli/cli.py`, the time helpers, offline tests.

Cut: generated `src/baml_client/` and `src/baml_src/`, the Open-WebUI functions and FastAPI server
(`src/open_webui_workspace/`, `src/server/`, `src/core/core_*`, `cli/run_server.py`, `cli/app.py`),
`notebooks/`, committed `outputs/`, `docs.md` (a stale copy of the upstream API), `INSTRUCTIONS.md`,
`poetry.lock`.

## Stack

- `-1` done: dead links, timestamp fixes, offline tests with a fake server (live tests behind
  `SCREENPIPE_LIVE=1`), CLI exit code, GitHub Actions.
- `-2` done: current screenpipe API (pipe routes, bearer auth via `SCREENPIPE_API_KEY`, new
  content types) and the matching CLI commands, tested against a fake server.
- `-3` planned: cut to client + CLI; Poetry to uv with a lockfile; `httpx` as the only dependency.
- `-4` planned: real package name, `screenpipe-client` console script, 30-second README.

## Applying a branch upstream

`b369f08` is the kranti-sandbox import commit. Run the first two lines in kranti-sandbox, the rest in
a clean upstream clone at `997496a`:

```bash
git format-patch --relative=screenpipe-python-client -o /tmp/spc-1 b369f08..screenpipe-python-client-1
git format-patch --relative=screenpipe-python-client -o /tmp/spc-2 screenpipe-python-client-1..screenpipe-python-client-2
cd screenpipe-python-client && git am /tmp/spc-1/*.patch    # then /tmp/spc-2, and so on
uv venv && uv pip install -e . pytest && .venv/bin/pytest -q
```

## Needs Tan

- Live tests and the Open-WebUI/LLM paths were not run: no screenpipe install or LLM key here.
- The `.github/workflows/test.yml` only runs once applied upstream (kranti-sandbox ignores nested workflows).
- Cutting the Open-WebUI pipe (`-3`) drops the code issue #48 is about; close it with a note if you agree.
