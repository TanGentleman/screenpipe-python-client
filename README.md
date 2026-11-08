# screenpipe-python-client

A Python client and CLI for the local REST API of [screenpipe](https://github.com/mediar-ai/screenpipe),
the open-source screen and audio recorder. Search what you saw and heard, check recorder health, and
manage tags and pipes from Python or the shell.

## Install

```bash
pip install git+https://github.com/TanGentleman/screenpipe-python-client
```

## Use

With screenpipe running on `localhost:3030`:

```bash
screenpipe-client health-check
screenpipe-client search --query standup --content-type audio --limit 5
```

```python
from screenpipe_client import ScreenpipeClient

with ScreenpipeClient() as client:
    results = client.search(query="standup", content_type="audio", limit=5)
    for hit in results["data"]:
        print(hit["type"], hit["content"]["timestamp"], hit["content"]["text"])
```

Methods return screenpipe's JSON, or `None` if the request fails (the error is logged). The CLI
prints the JSON and exits 1 on failure.

If screenpipe has API auth on, set `SCREENPIPE_API_KEY` (from `screenpipe auth token`), or pass
`api_key=` / `--api-key`. Use `--host` and `--port` for a non-default server.

## Commands

`search`, `health-check`, `list-audio-devices`, `list-monitors`, `add-tags-to-content`,
`remove-tags-from-content`, `list-pipes`, `get-pipe-info`, `install-pipe`, `enable-pipe`,
`disable-pipe`, `run-pipe`, `stop-pipe`. Run `screenpipe-client <command> --help` for options.

The client also has `add_content`, `execute_raw_sql`, `get_unnamed_speakers` and `update_speaker`.
screenpipe's routes are in
[server.rs](https://github.com/mediar-ai/screenpipe/blob/main/crates/screenpipe-engine/src/server.rs)
and the [API reference](https://docs.screenpi.pe/api-reference).

## Develop

```bash
uv sync
uv run pytest
```

The tests run against an in-process fake server, so they don't need screenpipe.

## License

MIT
