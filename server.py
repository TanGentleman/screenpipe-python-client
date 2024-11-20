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

from utils.owui_utils.configuration import create_config
from utils.owui_utils.pipeline_utils import get_inlet_body
from utils.owui_utils.constants import DEFAULT_QUERY

# Configure logging
logger = logging.getLogger(__name__)

# Type definitions


class Message(TypedDict):
    """Message type for chat interactions"""
    role: str
    content: str


class InletRequestBody(TypedDict):
    """Request body type for inlet endpoint"""
    messages: List[Message]
    stream: bool


class PipeRequestBody(TypedDict):
    """Request body type for pipe endpoints"""
    inlet_error: Optional[str]
    search_params: Optional[Dict[str, Any]]
    search_results: Optional[List[Any]]
    user_message_content: Optional[str]


class OutletRequestBody(TypedDict):
    """Request body type for outlet endpoint"""
    messages: List[Message]
    search_params: Optional[Dict[str, Any]]
    user_message_content: Optional[str]


class Models:
    """Model configuration constants"""
    FLASH_MODEL = "openrouter/google/gemini-flash-1.5-8b"
    SMART_MODEL = "Llama-3.1-70B"


# Configuration
FILTER_CONFIG = {
    # "LLM_API_BASE_URL": "http://localhost:4000/v1",
    # "JSON_MODEL": Models.FLASH_MODEL,
    # "FORCE_TOOL_CALLING": False,
    # "SCREENPIPE_SERVER_URL": "http://localhost:3030"
}

PIPE_CONFIG = {
    # "LLM_API_BASE_URL": "http://localhost:4000/v1",
    # "RESPONSE_MODEL": Models.FLASH_MODEL,
    # "GET_RESPONSE": True,
}

# Initialize FastAPI app and components
app = FastAPI(
    title="ScreenPipe API",
    description="API for processing data through ScreenPipe filters",
    version="1.0.0"
)

app_filter = ScreenFilter()
app_pipe = ScreenPipe()

app_filter.set_valves(FILTER_CONFIG)
app_pipe.set_valves(PIPE_CONFIG)

logger.info(
    "Filter valves:\n%s",
    pprint(
        app_filter.valves.model_dump(),
        indent=2))
logger.info("Pipe valves:\n%s", pprint(app_pipe.valves.model_dump(), indent=4))


@app.get("/")
async def root() -> Dict[str, str]:
    """Health check endpoint."""
    return {"message": "Hello World"}


@app.post("/filter/inlet")  # , response_model=FilterResponse)
async def filter_inlet(body: dict) -> dict:
    """Process incoming data through the inlet filter."""
    try:
        InletRequestBody(**body)
        logger.info("Processing filter inlet request")
        logger.debug("Request body: %s", body)
        logger.debug("Filter valves: %s", app_filter.valves)

        response_body = app_filter.inlet(body)
        return response_body
    except Exception as e:
        logger.error("Error in filter inlet: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipe/stream")
async def pipe_stream(body: dict) -> StreamingResponse:
    """Handle streaming pipe requests."""
    try:
        response = app_pipe.pipe(body)
        if not response:
            raise ValueError("Empty response from pipe")

        async def generate() -> AsyncGenerator[str, None]:
            """Generate streaming response chunks."""
            try:
                if isinstance(response, str):
                    yield f"data: {json.dumps(response)}\n\n"
                else:
                    for chunk in response:
                        if chunk:  # Only process non-None chunks
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
async def pipe_completion(body: dict) -> Dict[str, str]:
    """Handle non-streaming pipe completion requests."""
    try:
        response = app_pipe.pipe(body)
        if not isinstance(response, str):
            raise ValueError("Pipe must return a string")
        return {"response_string": response}
    except Exception as e:
        logger.error("Error in pipe completion: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/filter/outlet")  # , response_model=FilterResponse)
async def filter_outlet(body: dict) -> dict:
    """Process outgoing data through the outlet filter."""
    try:
        response_body = app_filter.outlet(body)
        return response_body
    except Exception as e:
        logger.error("Error in filter outlet: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/valves/update")
async def update_valves(
    filter_config: Dict[str, Any] = Body(None),
    pipe_config: Dict[str, Any] = Body(None)
) -> Dict[str, str]:
    """Update the valve configurations for filter and pipe components.

    Args:
        filter_config: Optional configuration dict for filter valves
        pipe_config: Optional configuration dict for pipe valves

    Returns:
        Dict containing success message and current valve configurations

    Raises:
        HTTPException: If valve update fails
    """
    try:
        if filter_config is not None:
            logger.info(
                "Updating filter valves with config: %s",
                filter_config)
            app_filter.set_valves(filter_config)

        if pipe_config is not None:
            logger.info("Updating pipe valves with config: %s", pipe_config)
            app_pipe.set_valves(pipe_config)

        return {
            "message": "Valves updated successfully",
            "filter_valves": str(app_filter.valves),
            "pipe_valves": str(app_pipe.valves)
        }
    except Exception as e:
        logger.error("Error updating valves: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update valves: {str(e)}"
        )


@app.get("/valves/refresh")
async def refresh_valves_from_env() -> Dict[str, str]:
    """Refresh valve configurations from environment variables.

    Returns:
        Dict containing success message and refreshed valve configurations

    Raises:
        HTTPException: If valve refresh fails
    """
    try:
        config = create_config()

        # Build filter config from env vars
        filter_config = {
            "LLM_API_BASE_URL": config.llm_api_base_url,
            "LLM_API_KEY": config.llm_api_key,
            "SCREENPIPE_SERVER_URL": config.screenpipe_server_url,
            "FORCE_TOOL_CALLING": config.force_tool_calling,
            "FILTER_MODEL": config.filter_model,
        }

        # Build pipe config from env vars
        pipe_config = {
            "LLM_API_BASE_URL": config.llm_api_base_url,
            "LLM_API_KEY": config.llm_api_key,
            "GET_RESPONSE": config.get_response,
            "RESPONSE_MODEL": config.response_model
        }

        # Update both components
        app_filter.set_valves(filter_config)
        app_pipe.set_valves(pipe_config)

        return {
            "message": "Valves updated successfully from environment",
            "filter_valves": str(app_filter.valves),
            "pipe_valves": str(app_pipe.valves)
        }

    except Exception as e:
        logger.error("Error updating valves from environment: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update valves from environment: {str(e)}"
        )


def process_api_stream_response(response: Any) -> str:
    """Process streaming response from HTTP request."""
    if not response or not response.ok:
        logger.error(f"Invalid response: {response}")
        return ""

    full_response = ""
    try:
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
                delta = chunk_data['choices'][0].get('delta', {})
                chunk_content = delta.get('content', '')

            if chunk_content:
                print(chunk_content, end="", flush=True)
                full_response += chunk_content

    except Exception as e:
        logger.error(f"Error processing stream response: {e}")

    print()
    return full_response


def run_pipeline(body: dict) -> None:
    """Run the pipeline with the given body."""
    try:
        # Process pipeline stages
        inlet_response = requests.post(
            "http://localhost:3333/filter/inlet", json=body)
        inlet_data = inlet_response.json()

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

        inlet_data["messages"].append(
            {"role": "assistant", "content": full_response})
        outlet_response = requests.post(
            "http://localhost:3333/filter/outlet",
            json=inlet_data
        )
        outlet_data = outlet_response.json()

        response_string = outlet_data["messages"][-1]["content"]
        print("\n\n")
        print(response_string)
        return response_string

    except Exception as e:
        logger.error("Error in server.run_pipeline: %s", str(e))


def main_from_cli(query: Optional[str] = None) -> None:
    """CLI entry point for testing the pipeline."""
    body = get_inlet_body(query=query)
    run_pipeline(body)


def start_server(port: int = 3333) -> None:
    """Start the FastAPI server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    import sys
    cli_query = " ".join(sys.argv[1:]) or None
    main_from_cli(cli_query)
