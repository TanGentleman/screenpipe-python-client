# screenpipe-python-client

A Python client and CLI for the local REST API of [screenpipe](https://github.com/screenpipe/screenpipe):
search what it captured from your screen and audio, check its health, and manage tags and pipes.

```sh
git clone https://github.com/TanGentleman/screenpipe-python-client && cd screenpipe-python-client
uv sync --locked
uv run screenpipe-client health-check
```

Needs Python 3.10+, [uv](https://docs.astral.sh/uv/) and a running screenpipe on `localhost:3030`;
every command except `health-check` also needs `SCREENPIPE_API_KEY`. Details:
[IMPLEMENTATION.md](IMPLEMENTATION.md), [ROADMAP.md](ROADMAP.md).

MIT licensed.
