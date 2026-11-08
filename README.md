# Screenpipe Python Client

A Python client library and CLI for the [screenpipe](https://github.com/mediar-ai/screenpipe) REST API.

## Installation

```bash
git clone https://github.com/TanGentleman/screenpipe-python-client.git
cd screenpipe-python-client
poetry install
```

## Quick Start

Verify the server connection:
```bash
poetry run python cli/cli.py health-check
```

Use `ScreenpipeClient` from `src/core/screenpipe.py` as the Python interface. The server's routes
are in [screenpipe-engine/src/server.rs](https://github.com/mediar-ai/screenpipe/blob/main/crates/screenpipe-engine/src/server.rs)
and the [API reference](https://docs.screenpi.pe/api-reference).

## CLI Commands

The CLI supports the following operations:

- `search`: Search content with filters
- `list-audio-devices`: List available audio devices
- `add-tags-to-content`: Add tags to content items
- `install-pipe`: Install a pipe from a URL or path
- `enable-pipe` / `disable-pipe`: Turn a pipe's schedule on or off
- `run-pipe`: Run a pipe once, now
- `stop-pipe`: Stop a pipe's current run
- `health-check`: Check server status
- `list-monitors`: List available monitors
- `list-pipes`: List available pipes
- `get-pipe-info`: Get pipe details
- `remove-tags-from-content`: Remove tags from content

If screenpipe has API auth on, set `SCREENPIPE_API_KEY` (from `screenpipe auth token`) or pass
`ScreenpipeClient(api_key=...)`.

For detailed usage and parameters, run:
```bash
python cli/cli.py --help
```

## Community

Have questions or found this useful? Feel free to:
- Reach out on Discord
- Open an issue or discussion on this repo

---
