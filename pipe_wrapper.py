import json
import logging
from pydantic import BaseModel, Field
import requests
from typing import Union, Generator, Iterator

IS_DOCKER = True
URL_BASE = "http://host.docker.internal" if IS_DOCKER else "http://localhost"
CORE_API_PORT = 3333
CORE_API_URL = f"{URL_BASE}:{CORE_API_PORT}"

DEFAULT_STREAMING = True


def yield_stream_response(response: requests.Response) -> Generator:
    """Yield lines from a streaming response"""
    if not response or not response.ok:
        logging.error(f"Invalid response: {response}")
        return

    for line in response.iter_lines():
        try:
            if not line:
                continue

            line = line.decode('utf-8')
            if not line.startswith('data: '):
                continue

            data = line[6:]  # Remove 'data: ' prefix
            if data == '[DONE]':
                continue

            chunk_data = json.loads(data)
            chunk_content = ""
            if isinstance(chunk_data, str):
                chunk_content = chunk_data
            elif isinstance(chunk_data, dict) and 'choices' in chunk_data:
                delta = chunk_data['choices'][0].get('delta', {})
                chunk_content = delta.get('content', '')

            if chunk_content:  # Only yield non-empty content
                yield chunk_content

        except Exception as e:
            logging.error(f"Error processing stream chunk: {e}")
            continue


class Pipe():
    """Pipe class for screenpipe functionality"""

    class Valves(BaseModel):
        api_url: str = Field(
            default=CORE_API_URL,
            description="Base URL for the Core API")
        stream: bool = Field(
            default=DEFAULT_STREAMING,
            description="Whether to stream the response")

    def __init__(self):
        self.type = "pipe"
        self.name = "wrapper_pipeline"
        self.valves = self.Valves()

    def pipe(self, body: dict) -> Union[str, Generator, Iterator]:
        """Main pipeline processing method"""
        try:
            if "stream" not in body:
                body["stream"] = self.valves.stream
            elif body["stream"] != self.valves.stream:
                # NOTE: Which one to use? Always use the one in the valves?
                # NOTE: Prioritizing valves over body
                logging.warning(
                    f"Stream value in body: {body['stream']} does not match valves: {self.valves.stream}!")
                logging.warning("Overriding with valves!")
                print("Setting stream to:", self.valves.stream)
                body["stream"] = self.valves.stream

            stream = body["stream"]
            if stream:
                response = requests.post(
                    f"{self.valves.api_url}/pipe/stream",
                    json=body,
                    stream=True
                )
                return yield_stream_response(response)
            else:
                response = requests.post(
                    f"{self.valves.api_url}/pipe/completion",
                    json=body
                )
                return response.json()["response_string"]

        except Exception as e:
            logging.error(f"Error in pipe: {type(e).__name__}")
            logging.error(f"Error details: {e}")
            return "An error occurred in the pipe."


if __name__ == "__main__":
    QUERY = "1 audio please. Tell me about it."
    STREAM = True
    pipe = Pipe()
    body = {"stream": STREAM, "messages": [{"role": "user", "content": QUERY}]}
    pipe_response = pipe.pipe(body)
    assert isinstance(pipe_response, str)
