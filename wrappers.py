import json
import logging
from pprint import pprint
import requests
from typing import Union, Generator, Iterator

IS_DOCKER = False
URL_BASE = "http://host.docker.internal" if IS_DOCKER else "http://localhost"
CORE_API_PORT = 3333
CORE_API_URL = f"{URL_BASE}:{CORE_API_PORT}"

def process_stream_response(response: requests.Response) -> str:
    """Process streaming response from HTTP request."""
    full_response = ""
    for line in response.iter_lines():
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
            chunk_content = chunk_data['choices'][0]['delta'].get('content', '')
        
        if chunk_content:
            print(chunk_content, end="", flush=True)
            full_response += chunk_content
            
    print()
    return full_response


class Filter():
    """Filter class for screenpipe functionality"""

    def __init__(self):
        self.type = "filter"
        self.name = "wrapper_filter"
        self.api_url = CORE_API_URL

    def inlet(self, body: dict) -> dict:
        """Inlet method for filter"""
        try:    
            response = requests.post(
                f"{self.api_url}/filter/inlet",
                json=body
            )
            return response.json()
        except Exception as e:
            logging.error(f"Error details: {e}")
            safe_details = f"Error in inlet: {type(e).__name__}"
            return {"inlet_error": safe_details}


    def outlet(self, body: dict) -> dict:
        """Outlet method for filter"""
        try:
            response = requests.post(
                f"{self.api_url}/filter/outlet",
                json=body
            )
            return response.json()
        except Exception as e:
            logging.error(f"Error details: {e}")
            safe_details = f"Error in outlet: {type(e).__name__}"
            return {"outlet_error": safe_details}

class Pipe():
    """Pipe class for screenpipe functionality"""

    def __init__(self):
        self.type = "pipe"
        self.name = "wrapper_pipeline"
        self.api_url = CORE_API_URL

    def pipe(self, body: dict) -> Union[str, Generator, Iterator]:
        """Main pipeline processing method"""
        try:
            stream = body.get("stream", False)
            
            if stream:
                response = requests.post(
                    f"{self.api_url}/pipe/stream",
                    json=body,
                    stream=True
                )
                return process_stream_response(response)
            else:
                response = requests.post(
                    f"{self.api_url}/pipe/completion",
                    json=body
                )
                return response.json()["response_string"]

        except Exception as e:
            logging.error(f"Error in pipe: {type(e).__name__}")
            logging.error(f"Error details: {e}")
            return "An error occurred in the pipe."

if __name__ == "__main__":
    QUERY = "1 audio please. Tell me about it."
    filter = Filter()
    pipe = Pipe()
    stream = True
    body = {"stream": stream, "messages": [{"role": "user", "content": QUERY}]}
    inlet_response = filter.inlet(body)
    pipe_response = pipe.pipe(inlet_response)
    assert isinstance(pipe_response, str)
    new_body = inlet_response
    new_body["messages"].append({"role": "assistant", "content": pipe_response})
    outlet_response = filter.outlet(new_body)
