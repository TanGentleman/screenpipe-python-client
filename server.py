import asyncio
import json
from pprint import pprint
from typing import Optional, List, Dict, AsyncGenerator
from typing_extensions import TypedDict
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from open_webui_workspace.screenpipe_filter_function import Filter as ScreenFilter
from open_webui_workspace.screenpipe_function import Pipe as ScreenPipe

# Type definitions
class Message(TypedDict):
    role: str
    content: str

class FilterResponse(TypedDict):
    messages: List[Message]
    stream: bool
    inlet_error: Optional[str]
    search_params: Optional[Dict]
    search_results: Optional[List]
    user_message_content: Optional[str]

class BaseRequestBody(TypedDict):
    messages: List[Message]
    stream: bool

class InletRequestBody(BaseRequestBody):
    pass

class PipeRequestBody(BaseRequestBody):
    inlet_error: Optional[str]
    search_params: Optional[Dict]
    search_results: Optional[List]
    user_message_content: Optional[str]

class OutletRequestBody(BaseRequestBody, total=False):
    search_params: Optional[Dict]
    search_results: Optional[List]
    user_message_content: Optional[str]

# Constants
SAMBANOVA_MODEL = "sambanova-llama-8b"
TINY_MODEL = "openrouter/meta-llama/llama-3.2-1b-instruct:free"

# Configuration
FILTER_CONFIG = {
    "LLM_API_BASE_URL": "http://localhost:4000/v1",
    "LLM_API_KEY": "sk-tan",
    "JSON_MODEL": SAMBANOVA_MODEL,
    "NATIVE_TOOL_CALLING": False,
    "SCREENPIPE_SERVER_URL": "http://localhost:3030"
}

PIPE_CONFIG = {
    "LLM_API_BASE_URL": "http://localhost:4000/v1",
    "LLM_API_KEY": "sk-tan",
    "RESPONSE_MODEL": TINY_MODEL,
    "GET_RESPONSE": True,
}

# Initialize FastAPI app and components
app = FastAPI()
app_filter = ScreenFilter()
app_pipe = ScreenPipe()

app_filter.valves = app_filter.Valves(**FILTER_CONFIG)
app_pipe.valves = app_pipe.Valves(**PIPE_CONFIG)

print("Filter valves:", app_filter.valves)
print("Pipe valves:", app_pipe.valves)

@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Hello World"}

@app.post("/filter/inlet")
async def filter_inlet(body: InletRequestBody) -> FilterResponse:
    try:
        print("Filter inlet")
        print("Body:", body)
        print("Filter valves:", app_filter.valves)
        
        response_body = app_filter.inlet(body)
        return FilterResponse(
            messages=response_body.get("messages", []),
            stream=response_body.get("stream", False),
            inlet_error=response_body.get("inlet_error"),
            search_params=response_body.get("search_params"),
            search_results=response_body.get("search_results"),
            user_message_content=response_body.get("user_message_content")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pipe/stream")
async def pipe_stream(body: PipeRequestBody) -> StreamingResponse:
    if not body["stream"]:
        raise HTTPException(status_code=400, detail="Use /pipe/completion for non-streaming requests")
        
    try:
        response = app_pipe.pipe(body)
        
        async def generate() -> AsyncGenerator[str, None]:
            try:
                for chunk in response:
                    if isinstance(chunk, str):
                        yield f"data: {json.dumps(chunk)}\n\n"
                    else:
                        yield f"data: {json.dumps(chunk.dict())}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# The completion pipe stores value in JSON with key "response_string"
@app.post("/pipe/completion")
async def pipe_completion(body: PipeRequestBody) -> Dict[str, str]:
    if body["stream"]:
        raise HTTPException(status_code=400, detail="Use /pipe/stream for streaming requests")
        
    try:
        response = app_pipe.pipe(body)
        if not isinstance(response, str):
            raise ValueError("Pipe must return a string")
        return {"response_string": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/filter/outlet")
async def filter_outlet(body: OutletRequestBody) -> FilterResponse:
    try:
        response_body = app_filter.outlet(body)
        return FilterResponse(
            messages=response_body.get("messages", []),
            stream=response_body.get("stream", False),
            inlet_error=response_body.get("inlet_error"),
            search_params=response_body.get("search_params"),
            search_results=response_body.get("search_results"),
            user_message_content=response_body.get("user_message_content")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def start_server(port: int = 3333) -> None:
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)

async def process_streaming_response(response_stream, body: Dict) -> str:
    full_response = ""
    for chunk in response_stream:
        chunk_content = ""
        if isinstance(chunk, str):
            chunk_content = chunk
            print(chunk, end="", flush=True)
        elif chunk.choices[0].delta.content is not None:
            chunk_content = chunk.choices[0].delta.content
            print(chunk_content, end="", flush=True)
        else:
            finish_reason = chunk.choices[0].finish_reason
            print(f"\n\nFinish reason: {finish_reason}\n")
        full_response += chunk_content
    print()
    return full_response

async def main() -> None:
    body = {
        "messages": [{"role": "user", "content": "What have I been doing in my past 5 ocr chunks?"}],
        "stream": True
    }
    PRINT_BODIES = False
    
    try:
        # Process pipeline stages
        inlet_response = await filter_inlet(body)
        if PRINT_BODIES:
            pprint(inlet_response)

        pipe_response = await pipe_stream(inlet_response)
        response = await process_streaming_response(pipe_response, inlet_response) if inlet_response["stream"] else pipe_response

        inlet_response["messages"].append({"role": "assistant", "content": response})
        outlet_response = await filter_outlet(inlet_response)
        
        if PRINT_BODIES:
            pprint(outlet_response)

        print("\n\n")
        print(outlet_response["messages"][-1]["content"])
    except Exception as e:
        print(f"Error: {e}")

def process_stream_response(response) -> str:
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
        elif 'choices' in chunk_data and chunk_data['choices'][0]['delta'].get('content'):
            chunk_content = chunk_data['choices'][0]['delta']['content']
        
        if chunk_content:
            print(chunk_content, end="", flush=True)
            full_response += chunk_content
            
    print()
    return full_response

def main_from_cli() -> None:
    import requests

    body = {
        "messages": [{"role": "user", "content": "What have I been doing in my past 2 audio chunks?"}],
        "stream": False
    }
    PRINT_BODIES = False

    try:
        # Process pipeline stages
        inlet_response = requests.post("http://localhost:3333/filter/inlet", json=body)
        inlet_data = inlet_response.json()
        if PRINT_BODIES:
            pprint(inlet_data)

        # Handle pipe response
        if inlet_data["stream"]:
            response = requests.post("http://localhost:3333/pipe/stream", json=inlet_data, stream=True)
            full_response = process_stream_response(response)
        else:
            response = requests.post("http://localhost:3333/pipe/completion", json=inlet_data)
            response_data = response.json()
            full_response = response_data["response_string"]
            print("Pipe output:")
            print(full_response)

        inlet_data["messages"].append({"role": "assistant", "content": full_response})
        outlet_response = requests.post("http://localhost:3333/filter/outlet", json=inlet_data)
        outlet_data = outlet_response.json()
        
        if PRINT_BODIES:
            pprint(outlet_data)

        print("\n\n")
        print(outlet_data["messages"][-1]["content"])

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # start_server()
    # asyncio.run(main())
    main_from_cli()
