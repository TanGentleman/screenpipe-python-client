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
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

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

### 3. Adding the Pipeline

1. Ensure Open-WebUI is running on port 8080
2. Navigate to: http://localhost:8080/workspace/functions
3. Create a new function by copying and pasting `full-function-pipe.py`
4. Configure the Valves by clicking the gear icon

### 4. Environment Configuration

Create a `.env` file with your configuration. Here's a sample configuration. I add these variables with a local LiteLLM proxy at port 4000:

```env
LITELLM_API_KEY=your-secret-key
RAG_EMBEDDING_ENGINE=ollama
AUDIO_STT_ENGINE=openai
OPENAI_API_BASE_URL=http://host.docker.internal:4000/v1
ENABLE_COMMUNITY_SHARING=False
ENABLE_MESSAGE_RATING=False
```

## Important Notes

- When using Docker, replace `localhost` with `host.docker.internal` in your URLs
- Using LiteLLM as a proxy is recommended for simplified base_url and model name management
- Run `test_valves.py` to verify your valve configurations are correct

## Troubleshooting

Before running the project:
1. Verify all components are installed correctly
2. Ensure environment variables are properly set
3. Confirm all services are running on their expected ports
