"""
title: Simple Search Pipeline
author: TanGentleman
author_url: https://github.com/TanGentleman
funding_url: https://github.com/TanGentleman
version: 0.2
"""
# NOTE: Add pipeline using OpenWebUI > Workspace > Functions > Add Function

# NOTE: This is a work in progress! Ideally, the config, helper functions
# and the tools should be separated. This is for convenient copy-pasting
# to OWUI.

### 1. IMPORTS ###
# Standard library imports
import logging
from dataclasses import dataclass
import os
import json
from datetime import datetime, timedelta, timezone
from typing import Generator, Iterator, List, Literal, Optional, Union, Tuple, Annotated

# Third-party imports
import requests
from langchain_core.utils.function_calling import convert_to_openai_tool
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

### 2. CONFIGURATION CONSTANTS ###
# NOTE: Sensitive - Sanitize before sharing
SENSITIVE_KEY = os.getenv('LITELLM_API_KEY', '')
if not SENSITIVE_KEY:
    raise ValueError("LITELLM_API_KEY environment variable is not set!")
REPLACEMENT_TUPLES = [
    # ("LASTNAME", ""),
    # ("FIRSTNAME", "NICKNAME")
]
# URL and Port Configuration
IS_DOCKER = True
DEFAULT_SCREENPIPE_PORT = 3030
URL_BASE = "http://localhost" if not IS_DOCKER else "http://host.docker.internal"

# LLM Configuration (openai compatible)
DEFAULT_LLM_API_BASE_URL = f"{URL_BASE}:4000/v1"
DEFAULT_LLM_API_KEY = SENSITIVE_KEY
DEFAULT_NATIVE_TOOL_CALLING = False
# NOTE: If NATIVE_TOOL_CALLING is True, tool model is used instead of the json model

# Model Configuration
DEFAULT_TOOL_MODEL = "Llama-3.1-70B"
DEFAULT_JSON_MODEL = "lmstudio-Llama-3.2-3B-4bit-MLX"

# NOTE: Model name must be valid for the endpoint:
# {DEFAULT_LLM_API_BASE_URL}/v1/chat/completions

# Time Configuration
PREFER_24_HOUR_FORMAT = True
DEFAULT_UTC_OFFSET = -7  # PDT

# System Messages
TOOL_SYSTEM_MESSAGE = """You are a helpful assistant that can access external functions. When performing searches, consider the current date and time, which is {current_time}. When appropriate, create a short search_substring to narrow down the search results."""

JSON_SYSTEM_MESSAGE = """You are a helpful assistant. Create a screenpipe search conforming to the correct JSON schema to search captured data stored in ScreenPipe's local database.

Create a JSON object ONLY for the properties field of the search parameters:
{schema}

If the time range is not relevant, use None for the start_time and end_time fields. Otherwise, they must be in ISO format matching the current time: {current_time}.

Construct an optimal search filter for the query. When appropriate, create a search_substring to narrow down the search results. Set a limit based on the user's request, or default to 5.

Example search JSON objects:
{examples}

ONLY Output the search JSON object, nothing else.
"""

@dataclass
class PipelineConfig:
    """Configuration management for Screenpipe Pipeline"""
    # API and Endpoint Configuration
    llm_api_base_url: str
    llm_api_key: str
    screenpipe_port: int
    is_docker: bool

    # Model Configuration
    tool_model: str
    json_model: str
    native_tool_calling: bool

    # Pipeline Settings
    prefer_24_hour_format: bool
    default_utc_offset: int

    # Sensitive Data
    replacement_tuples: List[Tuple[str, str]]

    @classmethod
    def from_env(cls) -> 'PipelineConfig':
        """Create configuration from environment variables with fallbacks.

        Returns:
            PipelineConfig: Configuration object populated from environment variables,
            falling back to default values if not set.
        """

        def get_bool_env(key: str, default: bool) -> bool:
            """Helper to consistently parse boolean environment variables"""
            return os.getenv(key, str(default)).lower() == 'true'

        def get_int_env(key: str, default: int) -> int:
            """Helper to consistently parse integer environment variables"""
            return int(os.getenv(key, default))

        return cls(
            # API and Endpoint Configuration
            llm_api_base_url=os.getenv(
                'LLM_API_BASE_URL', DEFAULT_LLM_API_BASE_URL),
            llm_api_key=os.getenv('LLM_API_KEY', DEFAULT_LLM_API_KEY),
            screenpipe_port=get_int_env(
                'SCREENPIPE_PORT', DEFAULT_SCREENPIPE_PORT),
            is_docker=get_bool_env('IS_DOCKER', IS_DOCKER),

            # Model Configuration
            tool_model=os.getenv('TOOL_MODEL', DEFAULT_TOOL_MODEL),
            json_model=os.getenv(
                'JSON_MODEL', DEFAULT_JSON_MODEL),
            native_tool_calling=get_bool_env('NATIVE_TOOL_CALLING', DEFAULT_NATIVE_TOOL_CALLING),

            # Pipeline Settings
            prefer_24_hour_format=get_bool_env(
                'PREFER_24_HOUR_FORMAT', PREFER_24_HOUR_FORMAT),
            default_utc_offset=get_int_env(
                'DEFAULT_UTC_OFFSET', DEFAULT_UTC_OFFSET),

            # Sensitive Data
            replacement_tuples=REPLACEMENT_TUPLES,
        )

    @property
    def screenpipe_server_url(self) -> str:
        """Compute the Screenpipe base URL based on configuration"""
        url_base = "http://localhost" if not self.is_docker else "http://host.docker.internal"
        return f"{url_base}:{self.screenpipe_port}"


EXAMPLE_SEARCH_JSON = """\
{
    "limit": 2,
    "content_type": "audio",
    "start_time": null,
    "end_time": null
}
{
    "limit": 1,
    "content_type": "all",
    "start_time": "2024-03-20T00:00:00Z",
    "end_time": "2024-03-20T23:59:59Z"
}"""


class SearchParameters(BaseModel):
    """Search parameters for the Screenpipe Pipeline"""
    limit: Annotated[int, Field(ge=1, le=100)] = Field(
        default=5,
        description="The maximum number of results to return (1-100)"
    )
    content_type: Literal["ocr", "audio", "all"] = Field(
        default="all",
        description="The type of content to search"
    )
    search_substring: Optional[str] = Field(
        default=None,
        description="Optional search term to filter results"
    )
    start_time: Optional[str] = Field(
        default=None,
        description="Start timestamp for search range (ISO format, e.g., 2024-03-20T00:00:00Z)"
    )
    end_time: Optional[str] = Field(
        default=None,
        description="End timestamp for search range (ISO format, e.g., 2024-03-20T23:59:59Z)"
    )
    app_name: Optional[str] = Field(
        default=None,
        description="Optional app name to filter results"
    )

def screenpipe_search(
    search_substring: str = "",
    content_type: Literal["ocr", "audio", "all"] = "all",
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 5,
    app_name: Optional[str] = None,
) -> dict:
    """Searches captured data stored in ScreenPipe's local database.

    Args:
        search_substring: Optional search term to filter results. Defaults to "".
        content_type: The type of content to search. Must be one of "ocr", "audio", or "all". Defaults to "all".
        start_time: Start timestamp for search range (ISO format, e.g., 2024-03-20T00:00:00Z). Defaults to None.
        end_time: End timestamp for search range (ISO format, e.g., 2024-03-20T23:59:59Z). Defaults to None.
        limit: The maximum number of results to return (1-100). Defaults to 5.
        app_name: Optional app name to filter results. Defaults to None.

    Returns:
        dict: A dictionary containing the search results or an error message.
    """
    return {}


class PipeSearch:
    """Search-related functionality for the Pipe class"""
    # Add default values for other search parameters

    def __init__(self, default_dict: dict = {}):
        self.default_dict = default_dict
        self.screenpipe_server_url = self.default_dict.get(
            "screenpipe_server_url", "")
        if not self.screenpipe_server_url:
            logging.warning(
                "ScreenPipe server URL not set in PipeSearch initialization")

    def search(self, **kwargs) -> dict:
        """Enhanced search wrapper with better error handling"""
        if not self.screenpipe_server_url:
            return {"error": "ScreenPipe server URL is not set"}

        try:
            # Validate and process search parameters
            params = self._process_search_params(kwargs)
            print("Params:", params)

            response = requests.get(
                f"{self.screenpipe_server_url}/search",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            results = response.json()

            return results if results.get("data") else {
                "error": "No results found"}

        except requests.exceptions.RequestException as e:
            logging.error(f"Search request failed: {e}")
            return {"error": f"Search failed: {str(e)}"}
        except Exception as e:
            logging.error(f"Unexpected error in search: {e}")
            return {"error": f"Unexpected error: {str(e)}"}

    def _process_search_params(self, params: dict) -> dict:
        """Process and validate search parameters"""
        # Extract and process search substring
        query = params.pop('search_substring', '')
        if query:
            params['q'] = query.strip() or None

        # Remove None values and process remaining parameters
        processed = {k: v for k, v in params.items() if v is not None}

        # Validate limit
        if 'limit' in processed:
            processed['limit'] = min(int(processed['limit']), 40)

        # Capitalize app name if present
        if 'app_name' in processed and processed['app_name']:
            processed['app_name'] = processed['app_name'].capitalize()

        return processed


class PipeUtils:
    """Utility methods for the Pipe class"""
    # TODO Add other response related methods here

    @staticmethod
    def remove_names(
            content: str, replacement_tuples: List[Tuple[str, str]] = []) -> str:
        for sensitive_word, replacement in replacement_tuples:
            content = content.replace(sensitive_word, replacement)
        return content

    @staticmethod
    def format_timestamp(
            timestamp: str,
            offset_hours: Optional[float] = -
            7) -> str:
        """Formats UTC timestamp to local time with optional offset (default -7 PDT)"""
        if not isinstance(timestamp, str):
            raise ValueError("Timestamp must be a string")

        try:
            dt = datetime.strptime(timestamp.split(
                '.')[0] + 'Z', "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            if offset_hours is not None:
                dt = dt + timedelta(hours=offset_hours)
            return dt.strftime("%m/%d/%y %H:%M")
        except ValueError:
            raise ValueError(f"Invalid timestamp format: {timestamp}")

    @staticmethod
    def sanitize_results(results: dict,
                         replacement_tuples: List[Tuple[str,
                                                        str]] = []) -> list[dict]:
        """Sanitize search results with improved error handling"""
        try:
            if not isinstance(results, dict) or "data" not in results:
                raise ValueError("Invalid results format")

            sanitized = []
            for result in results["data"]:
                sanitized_result = {
                    "timestamp": PipeUtils.format_timestamp(
                        result["content"]["timestamp"]),
                    "type": result["type"]}

                if result["type"] == "OCR":
                    sanitized_result.update({
                        "content": PipeUtils.remove_names(result["content"]["text"], replacement_tuples),
                        "app_name": result["content"]["app_name"],
                        "window_name": result["content"]["window_name"]
                    })
                elif result["type"] == "Audio":
                    sanitized_result.update({
                        "content": result["content"]["transcription"],
                        "device_name": result["content"]["device_name"]
                    })
                else:
                    raise ValueError(f"Unknown result type: {result['type']}")

                sanitized.append(sanitized_result)

            return sanitized

        except Exception as e:
            logging.error(f"Error sanitizing results: {str(e)}")
            return []

    @staticmethod
    def parse_schema_from_response(
            response_text: str,
            target_schema) -> dict | str:
        """
        Parses the response text into a dictionary using the provided Pydantic schema.

        Args:
            response_text (str): The response text to parse.
            schema (BaseModel): The Pydantic schema to validate the parsed data against.

        Returns:
            dict: The parsed and validated data as a dictionary. If parsing fails, returns an empty dictionary.
        """
        assert issubclass(
            target_schema, BaseModel), "Schema must be a Pydantic BaseModel"
        try:
            response_object = json.loads(response_text)
            pydantic_object = target_schema(**response_object)
            return pydantic_object.model_dump()
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"Error: {e}")
            return response_text

    @staticmethod
    def catch_malformed_tool(response_text: str) -> str | dict:
        """Parse response text to extract tool call if present, otherwise return original text."""
        TOOL_PREFIX = "<function=screenpipe_search>"

        if not response_text.startswith(TOOL_PREFIX):
            return response_text

        try:
            end_index = response_text.rfind("}")
            if end_index == -1:
                logging.warning("Warning: Malformed tool unable to be parsed!")
                return response_text

            # Extract and validate JSON arguments
            args_str = response_text[len(TOOL_PREFIX):end_index + 1]
            json.loads(args_str)  # Validate JSON format

            return {
                "id": f"call_{len(args_str)}",
                "type": "function",
                "function": {
                    "name": "screenpipe_search",
                    "arguments": args_str
                }
            }

        except json.JSONDecodeError:
            return response_text
        except Exception as e:
            print(f"Error parsing tool response: {e}")
            return "Failed to process function call"

    @staticmethod
    def get_current_time() -> str:
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")


class PipeBase:
    """Base class for Pipe functionality"""

    class Valves(BaseModel):
        """Valve settings for the Pipe"""
        LLM_API_BASE_URL: str = Field(
            default="", description="Base URL for the LLM API"
        )
        LLM_API_KEY: str = Field(
            default="", description="API key for LLM access"
        )
        TOOL_MODEL: str = Field(
            default="", description="Model to use for tool calls"
        )
        JSON_MODEL: Optional[str] = Field(
            default=None, description="JSON model path"
        )
        NATIVE_TOOL_CALLING: bool = Field(
            default=False, description="Works best with gpt-4o-mini, use JSON for local models."
        )
        SCREENPIPE_SERVER_URL: str = Field(
            default="", description="URL for the ScreenPipe server"
        )

    def __init__(self):
        self.type = "pipe"
        self.name = "screenpipe_pipeline"
        self.config = PipelineConfig.from_env()
        self.tools = [convert_to_openai_tool(screenpipe_search)]
        self.json_schema = SearchParameters.model_json_schema()
        self.replacement_tuples = self.config.replacement_tuples
        self.client = None
        self.initialize_valves()

    def initialize_valves(self):
        """Initialize valve settings"""
        self.valves = self.Valves(
            **{
                "LLM_API_BASE_URL": self.config.llm_api_base_url,
                "LLM_API_KEY": self.config.llm_api_key,
                "TOOL_MODEL": self.config.tool_model,
                "JSON_MODEL": self.config.json_model,
                "NATIVE_TOOL_CALLING": self.config.native_tool_calling,
                "SCREENPIPE_SERVER_URL": self.config.screenpipe_server_url,
            }
        )


class Pipe(PipeBase):
    """Main Pipe class implementing the pipeline functionality"""

    def pipe(self, body: dict) -> Union[str, Generator, Iterator]:
        """Main pipeline processing method"""
        try:
            self.initialize_settings()
            messages = self._prepare_initial_messages(body["messages"])

            # Get search results
            results = (self._tool_response_as_results_or_str(messages)
                       if self.native_tool_calling
                       else self._json_response_as_results_or_str(messages))

            if isinstance(results, str):
                return results

            # Process results
            sanitized_results = PipeUtils.sanitize_results(
                results, self.replacement_tuples)
            results_as_string = json.dumps(sanitized_results, indent=2)
            prepend_string = f"Found {len(sanitized_results)} search results:\n\n"
            return prepend_string + results_as_string

        except Exception as e:
            logging.error(f"Pipeline error: {str(e)}")
            # TODO: Add safe error handling like Filter.safe_log_error
            return f"An error occurred: {str(e)}"

    def initialize_settings(self):
        """Initialize all pipeline settings"""
        self._initialize_client()
        self._initialize_searcher()
        self._initialize_models()

    def _initialize_client(self):
        """Initialize OpenAI client"""
        base_url = self.valves.LLM_API_BASE_URL or self.config.llm_api_base_url
        api_key = self.valves.LLM_API_KEY or self.config.llm_api_key
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )

    def _initialize_searcher(self):
        """Initialize PipeSearch instance"""
        screenpipe_server_url = self.valves.SCREENPIPE_SERVER_URL or self.config.screenpipe_server_url
        default_dict = {"screenpipe_server_url": screenpipe_server_url}
        self.searcher = PipeSearch(default_dict)

    def _initialize_models(self):
        """Initialize model settings"""
        self.tool_model = self.valves.TOOL_MODEL or self.config.tool_model
        self.json_model = self.valves.JSON_MODEL or self.config.json_model
        self.native_tool_calling = self.valves.NATIVE_TOOL_CALLING

    def _prepare_initial_messages(self, messages):
        """Prepare initial messages for the pipeline"""
        if not messages or messages[-1]["role"] != "user":
            raise ValueError("Last message must be from the user!")

        current_time = PipeUtils.get_current_time()
        system_message = self._get_system_message(current_time)

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": messages[-1]["content"]}
        ]

    def _get_system_message(self, current_time: str) -> str:
        """Get appropriate system message based on configuration"""
        if self.native_tool_calling:
            return TOOL_SYSTEM_MESSAGE.format(current_time=current_time)
        return JSON_SYSTEM_MESSAGE.format(
            schema=self.json_schema,
            current_time=current_time,
            examples=EXAMPLE_SEARCH_JSON
        )

    def _tool_response_as_results_or_str(self, messages: list) -> str | dict:
        try:
            response = self._make_tool_api_call(messages)
            # Extract tool calls
            tool_calls = response.choices[0].message.model_dump().get(
                'tool_calls', [])
        except Exception:
            return "Failed tool api call."

        if not tool_calls:
            response_text = response.choices[0].message.content
            parsed_response = PipeUtils.catch_malformed_tool(response_text)
            if isinstance(parsed_response, str):
                return parsed_response
            parsed_tool_call = parsed_response
            assert isinstance(
                parsed_tool_call, dict), "Parsed tool must be dict"
            # RESPONSE is a tool
            tool_calls = [parsed_tool_call]

        if len(tool_calls) > 1:
            print("Max tool calls exceeded! Only the first tool call will be processed.")
            tool_calls = tool_calls[:1]
        results = self._process_tool_calls(tool_calls)
        # Can be a string or search_results dict
        return results

    def _get_json_response_format(self) -> dict:
        json_schema = self.json_schema
        lm_studio_condition = self.json_model.startswith("lmstudio")
        if lm_studio_condition:
            return {
                "type": "json_schema",
                "json_schema": {
                    "strict": True,
                    "schema": json_schema
                }
            }
        # Note: Ollama + OpenAI compatible
        return {"type": "json_object"}

    def _json_response_as_results_or_str(
            self, messages: list) -> str | dict:
        # Replace system message
        assert messages[0]["role"] == "system", "There should be a system message here!"
        # NOTE: Response format varies by provider
        print("Using json model:", self.json_model)
        try:
            response = self.client.chat.completions.create(
                model=self.json_model,
                messages=messages,
                response_format=self._get_json_response_format(),
            )
            response_text = response.choices[0].message.content
            parsed_search_schema = PipeUtils.parse_schema_from_response(
                response_text, SearchParameters)
            if isinstance(parsed_search_schema, str):
                return response_text

            function_args = parsed_search_schema
            print("Constructed search params:", function_args)
            search_results = self.searcher.search(**function_args)
            if not search_results:
                return "No results found"
            if "error" in search_results:
                return search_results["error"]
            return search_results
        except Exception:
            return "Failed json mode api call."

    def _make_tool_api_call(self, messages):
        print("Using tool model:", self.tool_model)
        return self.client.chat.completions.create(
            model=self.tool_model,
            messages=messages,
            tools=self.tools,
            tool_choice="auto",
            stream=False
        )

    def _process_tool_calls(self, tool_calls) -> dict | str:
        for tool_call in tool_calls:
            if tool_call['function']['name'] == 'screenpipe_search':
                function_args = json.loads(tool_call['function']['arguments'])
                search_results = self.searcher.search(**function_args)
                if not search_results:
                    return "No results found"
                if "error" in search_results:
                    return search_results["error"]
                return search_results
        raise ValueError("No valid tool call found")


def load_environment_variables():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("Warning: dotenv not found. Using default values.")


def main(prompt: str = "Create a search for audio content with a limit of 2."):
    pipe = Pipe()
    stream = False
    body = {"stream": stream, "messages": [
        {"role": "user", "content": prompt}]}
    if not stream:
        print("Non-streaming response:")
        print(pipe.pipe(body))


if __name__ == "__main__":
    load_environment_variables()
    main()
