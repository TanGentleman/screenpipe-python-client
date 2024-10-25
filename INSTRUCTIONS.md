To run the docker container:

```
docker run -d -p 8001:8080 \
-e WEBUI_NAME=Tan \
-e ENABLE_OLLAMA_API=False \
-e ENABLE_COMMUNITY_SHARING=False \
-e ENABLE_MESSAGE_RATING=False \
-e LITELLM_API_KEY=sk-tan \
-e RAG_EMBEDDING_ENGINE=ollama \
-e AUDIO_STT_ENGINE=openai \
-e OPENAI_API_BASE_URL=http://host.docker.internal:4000/v1 \
-v oct23-open-webui:/app/backend/data --name tan-open-webui ghcr.io/open-webui/open-webui:main
```

To copy the necessary files to the docker container:

```
docker exec -it open-webui /bin/sh
cd /app/backend/open_webui/utils
cp ~/Documents/GitHub/screenpipe-python-client/sp_utils.py .
cp ~/Documents/GitHub/screenpipe-python-client/screenpipe_client.py .
cp ~/Documents/GitHub/screenpipe-python-client/utils/secrets.py .
cp ~/Documents/GitHub/screenpipe-python-client/utils/constants.py .
```
