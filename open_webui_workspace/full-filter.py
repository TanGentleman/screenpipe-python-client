"""
title: Screenpipe Filter (Full)
author: TanGentleman
author_url: https://github.com/TanGentleman
funding_url: https://github.com/TanGentleman
version: 0.2
"""

# LAST UPDATED: 2024-11-14


### 1. IMPORTS ###
# Standard library imports
import logging
import json
from typing import Optional

# Third-party imports
from langchain_core.utils.function_calling import convert_to_openai_tool
from openai import OpenAI
from pydantic import BaseModel, Field

# Local imports
### PipelineConfig
### from utils.owui_utils.configuration import PipelineConfig
import os
from dataclasses import dataclass
from typing import List, Tuple

# Environment variables and defaults
SENSITIVE_KEY = os.getenv('LLM_API_KEY', '')
if not SENSITIVE_KEY:
    print("WARNING: LLM_API_KEY environment variable is not set!")

# Sensitive data replacements
REPLACEMENT_TUPLES = [
    # ("LASTNAME", ""),
    # ("FIRSTNAME", "NICKNAME")
]


# Configuration defaults
IS_DOCKER = True
DEFAULT_SCREENPIPE_PORT = 3030
URL_BASE = "http://host.docker.internal" if IS_DOCKER else "http://localhost"
DEFAULT_LLM_API_BASE_URL = f"{URL_BASE}:11434/v1"
DEFAULT_LLM_API_KEY = SENSITIVE_KEY or "API-KEY-HERE"

# Model settings
DEFAULT_TOOL_MODEL = "gpt-4o-mini"
DEFAULT_JSON_MODEL = "qwen2.5:3b" 
DEFAULT_RESPONSE_MODEL = "qwen2.5:3b"
DEFAULT_NATIVE_TOOL_CALLING = False
GET_RESPONSE = False

# Time settings
DEFAULT_UTC_OFFSET = -7  # PDT

@dataclass
class PipelineConfig:
    """Configuration management for Screenpipe Pipeline"""
    # API settings
    llm_api_base_url: str
    llm_api_key: str
    screenpipe_port: int
    is_docker: bool

    # Model settings  
    tool_model: str
    json_model: str
    native_tool_calling: bool
    get_response: bool
    response_model: str

    # Pipeline settings
    default_utc_offset: int
    replacement_tuples: List[Tuple[str, str]]

    @classmethod
    def from_env(cls) -> 'PipelineConfig':
        """Create configuration from environment variables with fallbacks."""
        def get_bool_env(key: str, default: bool) -> bool:
            return os.getenv(key, str(default)).lower() == 'true'

        def get_int_env(key: str, default: int) -> int:
            return int(os.getenv(key, default))

        return cls(
            llm_api_base_url=os.getenv('LLM_API_BASE_URL', DEFAULT_LLM_API_BASE_URL),
            llm_api_key=os.getenv('LLM_API_KEY', DEFAULT_LLM_API_KEY),
            screenpipe_port=get_int_env('SCREENPIPE_PORT', DEFAULT_SCREENPIPE_PORT),
            is_docker=get_bool_env('IS_DOCKER', IS_DOCKER),
            tool_model=os.getenv('TOOL_MODEL', DEFAULT_TOOL_MODEL),
            json_model=os.getenv('JSON_MODEL', DEFAULT_JSON_MODEL),
            native_tool_calling=get_bool_env('NATIVE_TOOL_CALLING', DEFAULT_NATIVE_TOOL_CALLING),
            get_response=get_bool_env('GET_RESPONSE', GET_RESPONSE),
            response_model=os.getenv('RESPONSE_MODEL', DEFAULT_RESPONSE_MODEL),
            default_utc_offset=get_int_env('DEFAULT_UTC_OFFSET', DEFAULT_UTC_OFFSET),
            replacement_tuples=REPLACEMENT_TUPLES,
        )

    @property
    def screenpipe_server_url(self) -> str:
        """Compute the Screenpipe base URL based on configuration"""
        url_base = "http://host.docker.internal" if self.is_docker else "http://localhost"
        return f"{url_base}:{self.screenpipe_port}"

### Constants
### from utils.owui_utils.constants import TOOL_SYSTEM_MESSAGE, JSON_SYSTEM_MESSAGE, EXAMPLE_SEARCH_JSON
# System Messages
TOOL_SYSTEM_MESSAGE = """You are a helpful assistant that can access external functions. When performing searches, consider the current date and time, which is {current_time}. When appropriate, create a short search_substring to narrow down the search results."""

JSON_SYSTEM_MESSAGE = """You are a helpful assistant. You will parse a user query to construct search parameters to search for chunks (audio, ocr, etc.) in ScreenPipe's local database.

Use the properties field below to construct the search parameters:
{schema}

Ensure the following rules are met:
    - limit must be between 1 and 100. defaults to 5 if not specified.
    - content_type must be one of: "ocr", "audio", "all"
    - time values should be null or in ISO format relative to the current timestamp: {current_time}

Example search JSON objects:
{examples}

ONLY Output the search JSON object, nothing else.
"""

EXAMPLE_SEARCH_JSON = """\
{
    "limit": 10,
    "content_type": "audio",
    "search_substring": "jason",
    "start_time": null,
    "end_time": null
}
{
    "limit": 1,
    "content_type": "all",
    "start_time": "2024-03-20T00:00:00Z",
    "end_time": "2024-03-20T23:59:59Z"
}"""

### PipelineUtils
### from utils.owui_utils.pipeline_utils import screenpipe_search, SearchParameters, PipeSearch, FilterUtils
from pydantic import BaseModel, Field
from typing import Literal, Optional, Annotated, List, Tuple
from datetime import datetime, timezone, timedelta
import logging
import requests
import json
from pydantic import ValidationError

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
    limit: int = 5,
    content_type: Literal["ocr", "audio", "all"] = "all",
    search_substring: str = "",
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
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

class FilterUtils:
    """Utility methods for the Filter class"""
    @staticmethod
    def get_current_time() -> str:
        """Get current time in ISO 8601 format with UTC timezone (e.g. 2024-01-23T15:30:45Z)"""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def remove_names(
            content: str, replacement_tuples: List[Tuple[str, str]] = []) -> str:
        """Replace sensitive words in content with their replacements."""
        for sensitive_word, replacement in replacement_tuples:
            content = content.replace(sensitive_word, replacement)
        return content

    @staticmethod
    def format_timestamp(
            timestamp: str,
            offset_hours: Optional[float] = None) -> str:
        """Formats ISO UTC timestamp to UTC time with optional hour offset.
        Args:
            timestamp (str): ISO UTC timestamp (YYYY-MM-DDTHH:MM:SS[.ssssss]Z)
            offset_hours (Optional[float]): Hours offset from UTC. None for UTC.
        Returns:
            str: Formatted as "MM/DD/YY HH:MM" (24-hour)
        Raises:
            ValueError: If invalid timestamp format
        """
        if not isinstance(timestamp, str):
            raise ValueError("Timestamp must be a string")

        try:
            dt = datetime.strptime(timestamp.split(
                '.')[0] + 'Z', "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError(f"Invalid timestamp format: {timestamp}")

        if offset_hours is not None:
            dt = dt + timedelta(hours=offset_hours)

        return dt.strftime("%m/%d/%y %H:%M")

    @staticmethod
    def is_chunk_rejected(content: str) -> bool:
        """Returns True if content is empty or a short 'thank you' message."""
        if not content:
            return True
        reject_length = 15
        is_rejected = len(content) < reject_length and "thank you" in content.lower()
        return is_rejected

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
                    "timestamp": FilterUtils.format_timestamp(
                        result["content"]["timestamp"]),
                    "type": result["type"]}

                if result["type"] == "OCR":
                    content_string = result["content"]["text"]
                    if FilterUtils.is_chunk_rejected(content_string):
                        continue
                    sanitized_result.update({
                        "content": FilterUtils.remove_names(content_string, replacement_tuples),
                        "app_name": result["content"]["app_name"],
                        "window_name": result["content"]["window_name"]
                    })

                elif result["type"] == "Audio":
                    content_string = result["content"]["transcription"]
                    if FilterUtils.is_chunk_rejected(content_string):
                        continue
                    sanitized_result.update({
                        "content": content_string,
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
            # NOTE: Maybe this should be {"error": "Failed to process function
            # call"}
            return "Failed to process function call"

    @staticmethod
    def _prepare_initial_messages(messages, system_message: str) -> List[dict]:
        """Prepare initial messages for the pipeline"""
        if not messages or messages[-1]["role"] != "user":
            raise ValueError("Last message must be from the user!")

        if not system_message:
            raise ValueError("System message must be provided")

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": messages[-1]["content"]}
        ]

# Attempt to import BAML utils if enabled
use_baml = True
construct_search_params = None

if use_baml:
    try:
        from utils.baml_utils import baml_generate_search_params
        logging.info("BAML search parameter construction enabled")
    except ImportError:
        use_baml = False
        pass

ENABLE_BAML = use_baml

class Filter:
    """Filter class for screenpipe functionality"""

    class Valves(BaseModel):
        """Valve settings for the Filter"""
        LLM_API_BASE_URL: str = Field(
            default="", description="Base URL for the LLM API"
        )
        LLM_API_KEY: str = Field(
            default="", description="API key for LLM access"
        )
        JSON_MODEL: Optional[str] = Field(
            default=None, description="Model to use for JSON calls"
        )
        TOOL_MODEL: str = Field(
            default="", description="Model to use for tool calls"
        )
        NATIVE_TOOL_CALLING: bool = Field(
            default=False,
            description="Works best with gpt-4o-mini, use JSON for other models.")
        SCREENPIPE_SERVER_URL: str = Field(
            default="", description="URL for the ScreenPipe server"
        )

    def __init__(self):
        self.name = "screenpipe_pipeline"
        self.config = PipelineConfig.from_env()
        self.tools = [convert_to_openai_tool(screenpipe_search)]
        self.json_schema = SearchParameters.model_json_schema()
        self.replacement_tuples = self.config.replacement_tuples
        self.valves = self.Valves(
            **{
                "LLM_API_BASE_URL": self.config.llm_api_base_url,
                "LLM_API_KEY": self.config.llm_api_key,
                "JSON_MODEL": self.config.json_model,
                "TOOL_MODEL": self.config.tool_model,
                "NATIVE_TOOL_CALLING": self.config.native_tool_calling,
                "SCREENPIPE_SERVER_URL": self.config.screenpipe_server_url,
            }
        )

    def safe_log_error(self, message: str, error: Exception) -> None:
        """Safely log an error without potentially exposing PII."""
        error_type = type(error).__name__
        logging.error(f"{message}: {error_type}")

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
        self.search_params = None

    def _initialize_models(self):
        """Initialize model settings"""
        self.tool_model = self.valves.TOOL_MODEL or self.config.tool_model
        self.json_model = self.valves.JSON_MODEL or self.config.json_model
        self.native_tool_calling = self.valves.NATIVE_TOOL_CALLING

    def _get_system_message(self) -> str:
        """Get appropriate system message based on configuration"""
        current_time = FilterUtils.get_current_time()
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
            parsed_response = FilterUtils.catch_malformed_tool(response_text)
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
        lm_studio_condition = self.json_model.startswith("lmstudio")
        if lm_studio_condition:
            assert self.json_schema is not None
            return {
                "type": "json_schema",
                "json_schema": {
                    "strict": True,
                    "schema": self.json_schema
                }
            }
        # Note: Ollama + OpenAI compatible
        return {"type": "json_object"}

    def _get_search_results_from_params(
            self, search_params: dict) -> dict | str:
        """Execute search using provided parameters and return results.

        Args:
            search_params: Dictionary containing search parameters like limit, content_type, etc.

        Returns:
            dict: Search results if successful
            str: Error message if search fails or no results found
        """
        # NOTE: validate search_params here
        print("Constructed search params:", search_params)
        self.search_params = search_params
        search_results = self.searcher.search(**search_params)
        if not search_results:
            return "No results found"
        if "error" in search_results:
            return search_results["error"]
        return search_results

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
            parsed_search_schema = FilterUtils.parse_schema_from_response(
                response_text, SearchParameters)
            if isinstance(parsed_search_schema, str):
                return response_text
            search_params = parsed_search_schema
            return self._get_search_results_from_params(search_params)
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
                search_params = function_args
                return self._get_search_results_from_params(search_params)
        raise ValueError("No valid tool call found")

    def _get_search_results(self, messages: list[dict]) -> dict:
        if ENABLE_BAML:
            raw_query = messages[-1]["content"]
            current_iso_timestamp = FilterUtils.get_current_time()
            results = baml_generate_search_params(raw_query, current_iso_timestamp)
            if isinstance(results, str):
                return results
            search_params = results.model_dump()
            return self._get_search_results_from_params(search_params)

        # Refactor user message
        user_message = messages[-1]["content"]
        user_message_refactored = FilterUtils.refactor_user_message(user_message)
        messages[-1]["content"] = user_message_refactored
        system_message = self._get_system_message()
        messages = FilterUtils._prepare_initial_messages(
            messages, system_message)
        if self.native_tool_calling:
            return self._tool_response_as_results_or_str(messages)
        else:
            return self._json_response_as_results_or_str(messages)

    def inlet_body_is_valid(self, body: dict) -> bool:
        """Check if the inlet body is valid"""
        messages = body.get("messages", [])
        return (len(messages) >= 2 and 
                messages[-2]["role"] == "assistant" and 
                messages[-1]["role"] == "user")

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """Process incoming messages, performing search and sanitizing results."""
        if not self.inlet_body_is_valid(body):
            body["inlet_error"] = "Invalid inlet body"
            return body
        original_messages = body["messages"]
        body["inlet_error"] = None
        body["search_params"] = None
        body["search_results"] = None
        body["user_message_content"] = original_messages[-1]["content"]
        try:
            # Initialize settings and prepare messages
            self.initialize_settings()
            results = self._get_search_results(original_messages)
            if not results:
                body["inlet_error"] = "No results found"
                return body
            # Handle error case
            if isinstance(results, str):
                body["inlet_error"] = results
                return body

            assert self.search_params is not None
            # Store search params
            body["search_params"] = self.search_params

            # Sanitize and store results
            sanitized_results = FilterUtils.sanitize_results(
                results, self.replacement_tuples)
            
            if not sanitized_results:
                body["inlet_error"] = "No sanitized results found"
                return body
            
            body["search_results"] = sanitized_results
            # Store original user message
            REPLACE_USER_MESSAGE = False
            if REPLACE_USER_MESSAGE:
                # NOTE: This REPLACES the user message in the body dictionary
                
                # Append search params to user message
                search_params_as_string = json.dumps(self.search_params, indent=2)
                prologue = "Search parameters:"
                refactored_last_message = original_messages[-1]["content"] + "\n\n" + \
                    prologue + "\n" + search_params_as_string
                original_messages[-1]["content"] = refactored_last_message
        except Exception as e:
            self.safe_log_error("Error processing inlet", e)
            body["inlet_error"] = "Error in Filter inlet!"

        return body

    def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """Process outgoing messages, incorporating sanitized results if available."""
        try:
            # Validate required fields exist
            messages = body.get("messages", [])
            if not messages:
                raise ValueError("Messages are empty in body")

            # Safely get last messages
            if len(messages) >= 2:
                last_message = messages[-1]
                last_user_message = messages[-2]

                # Restore original user message if available
                if last_user_message.get("role") == "user":
                    user_message_content = body.get("user_message_content")
                    if user_message_content is not None:
                        last_user_message["content"] = user_message_content

                # Add outlet marker to assistant message
                if last_message.get("role") == "assistant":
                    content = last_message.get("content", "")
                    if self.search_params:
                        pruned_search_params = {k: v for k, v in self.search_params.items() if v is not None}
                        search_params_as_string = json.dumps(pruned_search_params, indent=2)
                        last_message["content"] = content + f"\n\nUsed search params:\n{search_params_as_string}"
                    else:
                        last_message["content"] = content + "\n\nOUTLET active."

        except Exception as e:
            self.safe_log_error("Error processing outlet", e)

        return body
