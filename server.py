"""FastAPI server implementation for ScreenPipe API.

This module provides the HTTP API endpoints for the ScreenPipe service,
handling filtering and processing of data through inlet/outlet pipes.
"""

    
import requests
import json
import logging
from pprint import pprint
from typing import Optional, List, Dict, AsyncGenerator, Any
from typing_extensions import TypedDict
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import StreamingResponse
from open_webui_workspace.screenpipe_filter_function import Filter as ScreenFilter
from open_webui_workspace.screenpipe_function import Pipe as ScreenPipe

DEFAULT_QUERY = "What have I been doing on my laptop? Analyze 10 ocr chunks from the past 5 days."

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type definitions
class Message(TypedDict):
    """Message type for chat interactions"""
    role: str
    content: str

class FilterResponse(TypedDict, total=False):
    """Response type for filter endpoints"""
    messages: List[Message]
    stream: bool
    inlet_error: Optional[str]
    search_params: Optional[Dict[str, Any]]
    search_results: Optional[List[Any]]
    user_message_content: Optional[str]

class BaseRequestBody(TypedDict):
    """Base request body type"""
    messages: List[Message]
    stream: bool

class InletRequestBody(BaseRequestBody):
    """Request body type for inlet endpoint"""
    pass

class PipeRequestBody(BaseRequestBody, total=False):
    """Request body type for pipe endpoints"""
    inlet_error: Optional[str]
    search_params: Optional[Dict[str, Any]]
    search_results: Optional[List[Any]]
    user_message_content: Optional[str]

class OutletRequestBody(BaseRequestBody, total=False):
    """Request body type for outlet endpoint"""
    search_params: Optional[Dict[str, Any]]
    search_results: Optional[List[Any]]
    user_message_content: Optional[str]

class Models:
    """Model configuration constants"""
    FLASH_MODEL = "openrouter/google/gemini-flash-1.5-8b"
    SMART_MODEL = "Llama-3.1-70B"

# Configuration
FILTER_CONFIG = {
    "LLM_API_BASE_URL": "http://localhost:4000/v1",
    "JSON_MODEL": Models.FLASH_MODEL,
    "TOOL_MODEL": Models.SMART_MODEL,
    "NATIVE_TOOL_CALLING": False,
    "SCREENPIPE_SERVER_URL": "http://localhost:3030"
}

PIPE_CONFIG = {
    "LLM_API_BASE_URL": "http://localhost:4000/v1",
    "RESPONSE_MODEL": Models.FLASH_MODEL,
    "GET_RESPONSE": True,
}

# Initialize FastAPI app and components
app = FastAPI(
    title="ScreenPipe API",
    description="API for processing data through ScreenPipe filters",
    version="1.0.0"
)

app_filter = ScreenFilter()
app_pipe = ScreenPipe()

app_filter.valves = app_filter.Valves(**FILTER_CONFIG)
app_pipe.valves = app_pipe.Valves(**PIPE_CONFIG)

logger.info("Filter valves: %s", app_filter.valves)
logger.info("Pipe valves: %s", app_pipe.valves)

@app.get("/")
async def root() -> Dict[str, str]:
    """Health check endpoint."""
    return {"message": "Hello World"}

@app.post("/filter/inlet", response_model=FilterResponse)
async def filter_inlet(body: InletRequestBody) -> FilterResponse:
    """Process incoming data through the inlet filter."""
    try:
        logger.info("Processing filter inlet request")
        logger.debug("Request body: %s", body)
        logger.debug("Filter valves: %s", app_filter.valves)
        
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
        logger.error("Error in filter inlet: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pipe/stream")
async def pipe_stream(body: PipeRequestBody) -> StreamingResponse:
    """Handle streaming pipe requests."""
    if not body["stream"]:
        raise HTTPException(
            status_code=400,
            detail="Use /pipe/completion for non-streaming requests"
        )
        
    try:
        response = app_pipe.pipe(body)
        
        async def generate() -> AsyncGenerator[str, None]:
            """Generate streaming response chunks."""
            try:
                for chunk in response:
                    if isinstance(chunk, str):
                        yield f"data: {json.dumps(chunk)}\n\n"
                    else:
                        yield f"data: {json.dumps(chunk.dict())}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error("Error in stream generation: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e))
                
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error("Error in pipe stream: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pipe/completion")
async def pipe_completion(body: PipeRequestBody) -> Dict[str, str]:
    """Handle non-streaming pipe completion requests."""
    if body["stream"]:
        raise HTTPException(
            status_code=400,
            detail="Use /pipe/stream for streaming requests"
        )
        
    try:
        response = app_pipe.pipe(body)
        if not isinstance(response, str):
            raise ValueError("Pipe must return a string")
        return {"response_string": response}
    except Exception as e:
        logger.error("Error in pipe completion: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/filter/outlet", response_model=FilterResponse)
async def filter_outlet(body: OutletRequestBody) -> FilterResponse:
    """Process outgoing data through the outlet filter."""
    try:
        response_body = app_filter.outlet(body)
        return FilterResponse(
            messages=response_body.get("messages", []),
            stream=response_body.get("stream", False),
            search_params=response_body.get("search_params"),
            search_results=response_body.get("search_results"),
            user_message_content=response_body.get("user_message_content")
        )
    except Exception as e:
        logger.error("Error in filter outlet: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update_valves")
async def update_valves(
    filter_config: Dict[str, Any] = Body(None),
    pipe_config: Dict[str, Any] = Body(None)
) -> Dict[str, str]:
    """Update the valve configurations for filter and pipe components."""
    try:
        if filter_config:
            logger.info("Updating filter valves with config: %s", filter_config)
            new_filter_valves = app_filter.Valves(**filter_config)
            app_filter.valves = new_filter_valves
            
        if pipe_config:
            logger.info("Updating pipe valves with config: %s", pipe_config)
            new_pipe_valves = app_pipe.Valves(**pipe_config)
            app_pipe.valves = new_pipe_valves
            
        return {
            "message": "Valves updated successfully",
            "filter_valves": str(app_filter.valves),
            "pipe_valves": str(app_pipe.valves)
        }
    except Exception as e:
        logger.error("Error updating valves: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))



def process_api_stream_response(response: Any) -> str:
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
        elif 'choices' in chunk_data and chunk_data['choices'][0]['delta'].get('content'):
            chunk_content = chunk_data['choices'][0]['delta']['content']
        
        if chunk_content:
            print(chunk_content, end="", flush=True)
            full_response += chunk_content
            
    print()
    return full_response

def main_from_cli(query: Optional[str] = None) -> None:
    """CLI entry point for testing the pipeline."""
    if not query:
        query = DEFAULT_QUERY

    body = {
        "messages": [{"role": "user", "content": query}],
        "stream": True
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
            response = requests.post(
                "http://localhost:3333/pipe/stream",
                json=inlet_data,
                stream=True
            )
            full_response = process_api_stream_response(response)
        else:
            response = requests.post(
                "http://localhost:3333/pipe/completion",
                json=inlet_data
            )
            response_data = response.json()
            full_response = response_data["response_string"]
            print("Pipe output:")
            print(full_response)

        inlet_data["messages"].append({"role": "assistant", "content": full_response})
        outlet_response = requests.post(
            "http://localhost:3333/filter/outlet",
            json=inlet_data
        )
        outlet_data = outlet_response.json()
        
        if PRINT_BODIES:
            pprint(outlet_data)

        print("\n\n")
        print(outlet_data["messages"][-1]["content"])

    except Exception as e:
        logger.error("Error in CLI main: %s", str(e))

def start_server(port: int = 3333) -> None:
    """Start the FastAPI server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    import sys
    QUERY = " ".join(sys.argv[1:])
    print(f"Query:<{QUERY}>")
    main_from_cli(QUERY)
