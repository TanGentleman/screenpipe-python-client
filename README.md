# Screenpipe Python Client

A Python client library and CLI tool for interacting with the Screenpipe API. This client provides an intuitive interface for developers to integrate with and test Screenpipe functionality. No desktop app required.

> **New**: Open-WebUI integration is now available for testing! Detailed guides coming soon.

## Features

- Complete Python SDK for Screenpipe API integration
- Command-line interface for testing and troubleshooting
- Robust Open-WebUI integration and proxy server
- Comprehensive API for Agentic use cases

## Installation

```bash
cd screenpipe_python_client
poetry install
```

## Quick Start

Verify the server connection:
```bash
poetry run python cli/cli.py health-check
```

For developers:
- See `INSTRUCTIONS.md` for getting started
- Check the `open-webui-workspace` folder for Open-WebUI integration
- Use ScreenpipeClient from `src/utils/screenpipe.py` as your Python SDK
- Reference `docs.md` for under-the-hood API documentation (based on [screenpipe-server source](https://github.com/mediar-ai/screenpipe/blob/main/screenpipe-server/src/server.rs))

## CLI Commands

The CLI supports the following operations:

- `search`: Search content with filters
- `list-audio-devices`: List available audio devices
- `add-tags-to-content`: Add tags to content items
- `download-pipe`: Download a pipe configuration
- `run-pipe`: Execute a pipe
- `stop-pipe`: Stop a running pipe
- `health-check`: Check server status
- `list-monitors`: List available monitors
- `list-pipes`: List available pipes
- `get-pipe-info`: Get pipe details
- `remove-tags-from-content`: Remove tags from content

For detailed usage and parameters, run:
```bash
python cli/cli.py --help
```

## Community

Have questions or found this useful? Feel free to:
- Reach out on Discord
- Open an issue or discussion on this repo

---
