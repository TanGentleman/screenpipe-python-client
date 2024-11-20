# Project Setup Guide

This guide will walk you through setting up and running this project. The setup consists of two main components:
- Screenpipe
- Open-WebUI

## Quick Start

1. Install Screenpipe
2. Install Open-WebUI
3. Add a pipeline from this repo as an Open-WebUI Function
4. Configure your environment

## Detailed Installation Steps

### 1. Installing Screenpipe

**For Mac (using Homebrew):**
```bash
brew tap mediar-ai/screenpipe https://github.com/mediar-ai/screenpipe.git
brew install screenpipe
```

### 2. Installing Open-WebUI

#### Option A: Docker Installation (Recommended)
```bash
docker run -d \
  -p 8080:8080 \
  -e WEBUI_AUTH=false \
  -e TASK_MODEL_EXTERNAL="qwen2.5:3b" \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

### 3. Setting up the Python Client

#### Option A: Using Poetry (Recommended)

```bash
cd screenpipe_python_client
poetry install
```

#### Option B: Using Pip
```bash
cd screenpipe_python_client
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Please check out the `src/open-webui-workspace/README.md` for more information on how to configure Open-WebUI.

### 3. Adding the Pipeline

1. Ensure Open-WebUI is running on port 8080
2. Navigate to http://localhost:8080/workspace/functions
3. Create a new function by copying and pasting the Filter and Pipe from `src/open-webui-workspace/`
4. Configure the Valves by clicking the gear icon

### 4. Environment Configuration and Running the Server

Create a `.env` file with your configuration. Then run the server from the root directory with `python cli/run_server.py`

## Important Notes

- When using Docker, replace `localhost` with `host.docker.internal` in your URLs
- Using LiteLLM as a proxy is recommended for simplified base_url and model name management
- Run `tests/unit/test_valves.py` to verify your valve configurations are correct
- I recommend setting an external task model in Open-WebUI or disabling title/tag generation.

## Troubleshooting

Before running the project:
1. Test out the base url and api key in Open WebUI! Set the same values in your valves!!
2. If preferred, set defaults in utils/owui_utils/configuration.py or in full-pipe.py or full-filter.py
3. Confirm all services are running on their expected ports


To add the owui_utils subfolder to the Open-WebUI container:
Docker copying:
```bash
cd screenpipe-python-client
docker cp utils/owui_utils nov8-open-webui:app/backend/open_webui/utils
```

Alternative Open-WebUI Installation:
#### Option B: Installation from Source
```bash
# Clone and build the project
git clone https://github.com/open-webui/open-webui.git
cd open-webui
npm install
npm run build

# Set up Python environment
cd ./backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -U

# Run the application
bash start.sh
```