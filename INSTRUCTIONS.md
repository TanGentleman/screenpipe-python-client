Welcome! I'm glad you're here. This is how I run my setup. See below for other ways to use this project.

1: Install screenpipe
2: Install open-webui
3. Add a pipeline from this repo as an open-webui Function
4. Enjoy!

Note: I highly recommend using docker to run open-webui. When doing so, make sure the localhost url references are updated to be host.docker.internal instead of localhost. To simplify base_url and model name headaches, I recommend using LiteLLM as a simple proxy for your requests.

Detailed instructions below:

Simple Mac Install for screenpipe:
```
brew tap mediar-ai/screenpipe https://github.com/mediar-ai/screenpipe.git
brew install screenpipe
```

Simple Docker Install for open-webui on port 8080:
```
docker run -d -p 8080:8080 -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
```
(Optional) Add the -e flags with your environment variables. I use a local LiteLLM proxy at port 4000 to route my API requests.

Adding a fully functional pipeline to open-webui:
1. Start open-webui on port 8080
2. Access the workspace functions: http://localhost:8080/workspace/functions
3. Copy + paste full-function-pipe.py as a new function
4. Clear the gear icon and adjust the Valves to set the models.


(Optional) Install Open-Webui from source:
```
git clone https://github.com/open-webui/open-webui.git
cd open-webui
npm install
npm run build
cd ./backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -U
```

Run Open-Webui from source:
Pre-Req: Populate .env with your environment variables (My templates will be made accessible soon)
```
cd ./backend
source .venv/bin/activate
bash start.sh
```

My Environment Variables (for my use case + reduce bloat):
```
LITELLM_API_KEY=secret-key
RAG_EMBEDDING_ENGINE=ollama
AUDIO_STT_ENGINE=openai
OPENAI_API_BASE_URL=http://host.docker.internal:4000/v1
ENABLE_COMMUNITY_SHARING=False
ENABLE_MESSAGE_RATING=False
```
