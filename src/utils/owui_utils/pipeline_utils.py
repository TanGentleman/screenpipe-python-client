import os
from pydantic import BaseModel, Field
from typing import Literal, Optional, Annotated, List, Tuple
from datetime import datetime, timezone, timedelta
import logging
import requests
import json

from .constants import DEFAULT_QUERY, DEFAULT_STREAM, EXAMPLE_SEARCH_PARAMS, EXAMPLE_SEARCH_RESULTS, FINAL_RESPONSE_SYSTEM_MESSAGE, FINAL_RESPONSE_USER_MESSAGE

MAX_SEARCH_LIMIT = 99


def get_pipe_body(
    query: Optional[str] = None,
    stream: Optional[bool] = None,
    search_results: Optional[list] = None,
    search_params: Optional[dict] = None
) -> dict:
    """Creates a pipe request body for the ScreenPipe API.

    Args:
        query (Optional[str]): The user's query message. Defaults to DEFAULT_QUERY.
        stream (Optional[bool]): Whether to stream the response. Defaults to DEFAULT_STREAM.
        search_results (Optional[list]): Search results to include. Defaults to EXAMPLE_SEARCH_RESULTS.
        search_params (Optional[dict]): Search parameters used. Defaults to EXAMPLE_SEARCH_RESULTS.

    Returns:
        dict: A pipe request body containing:
            - user_message_content: The user's query message
            - search_results: List of search results
            - search_params: Dictionary of search parameters
            - stream: Boolean indicating whether to stream response
    """
    return {
        "user_message_content": query or DEFAULT_QUERY,
        "search_results": search_results or EXAMPLE_SEARCH_RESULTS,
        "search_params": search_params or EXAMPLE_SEARCH_PARAMS,
        "stream": stream if stream is not None else DEFAULT_STREAM,
        "inlet_error": None
    }


def get_inlet_body(
        query: Optional[str] = None,
        stream: Optional[bool] = None) -> dict:
    """Creates an inlet request body for the ScreenPipe API.

    Args:
        query (Optional[str]): The user's query message. Defaults to DEFAULT_QUERY.
        stream (Optional[bool]): Whether to stream the response. Defaults to DEFAULT_STREAM.

    Returns:
        dict: An inlet request body containing:
            - messages: List with single user message
            - stream: Boolean indicating whether to stream response
    """
    return {
        "messages": [{"role": "user", "content": query or DEFAULT_QUERY}],
        "stream": DEFAULT_STREAM if stream is None else stream
    }


class SearchParameters(BaseModel):
    """Search parameters for the Screenpipe Pipeline"""
    content_type: Literal["OCR", "AUDIO", "ALL"] = Field(
        description="Type of screen/audio content to search for, default to ALL"
    )
    from_time: Optional[str] = Field(
        default=None,
        description="ISO timestamp to filter results after this time"
    )
    to_time: Optional[str] = Field(
        default=None,
        description="ISO timestamp to filter results before this time"
    )
    limit: Optional[int] = Field(
        default=None,
        description="Maximum number of results to return"
    )
    search_substring: Optional[str] = Field(
        default=None,
        description="Optional substring to filter text content"
    )
    application: Optional[str] = Field(
        default=None,
        description="Optional filter to only show results from this application")

    def to_dict(self) -> dict:
        """Convert SearchParameters to a dictionary."""
        values = {k: v for k, v in self.model_dump().items() if v is not None}
        return values

    def to_api_dict(self) -> dict:
        """Convert SearchParameters to a dictionary mapped to the search API parameters.

        Transforms the parameters to match the API requirements:
        - Maps field names to API parameter names
        - Converts content_type to lowercase
        - Removes None values
        - Validates against ScreenPipeAPISearch schema

        Returns:
            dict: A dictionary containing the mapped API parameters
        """
        # Define mapping of model fields to API parameter names
        API_PARAM_MAP = {
            'search_substring': 'q',
            'content_type': 'content_type',
            'limit': 'limit',
            'from_time': 'start_time',
            'to_time': 'end_time',
            'application': 'app_name'
        }

        # Get non-None values
        values = self.to_dict()

        # Transform and map values to API parameters
        search_params = {}
        for field_name, value in values.items():
            if field_name not in API_PARAM_MAP:
                print(
                    f"WARNING: Field name not in API_PARAM_MAP: {field_name}")
                continue

            api_param = API_PARAM_MAP[field_name]

            # Handle content_type special case
            if field_name == 'content_type':
                value = value.lower()
            
            # Format timestamps to include time component
            if field_name in ['from_time', 'to_time']:
                if not value.endswith('Z') and 'T' not in value:
                    # Add time component if missing
                    try:
                        # Validate date format (YYYY-MM-DD)
                        year, month, day = value.split('-')
                        if not (len(year) == 4 and len(month) == 2 and len(day) == 2):
                            raise ValueError
                        value = f"{value}T00:00:00Z" if field_name == 'from_time' else f"{value}T23:59:59Z"
                    except ValueError:
                        raise ValueError(f"Invalid date format: {value}. Expected YYYY-MM-DD")
                    
            search_params[api_param] = value

        # Validate against API schema
        validated_params = ScreenPipeAPISearch(**search_params).to_api_dict()
        if not validated_params == search_params:
            logging.error("API parameter validation failed!!!")
            print("Validated params:", validated_params)
            print("Search params:", search_params)
            raise AssertionError("API parameter validation failed")

        return search_params


class ScreenPipeAPISearch(BaseModel):
    """API search parameters for the Screenpipe server"""
    q: Optional[str] = Field(
        default=None,
        description="Search term to filter content"
    )
    content_type: Literal["ocr", "audio", "fts", "ui", "all"] = Field(
        description="Type of content to search for"
    )
    limit: Optional[int] = Field(
        default=None,  # 20 is default for API
        description="Maximum number of results per page"
    )
    offset: Optional[int] = Field(
        default=None,
        description="Pagination offset"
    )
    start_time: Optional[str] = Field(
        default=None,
        description="ISO timestamp to filter results after this time"
    )
    end_time: Optional[str] = Field(
        default=None,
        description="ISO timestamp to filter results before this time"
    )
    app_name: Optional[str] = Field(
        default=None,
        description="Filter results by application name"
    )
    window_name: Optional[str] = Field(
        default=None,
        description="Filter results by window name"
    )
    include_frames: Optional[bool] = Field(
        default=None,
        description="Include base64 encoded frames in results"
    )
    min_length: Optional[int] = Field(
        default=None,
        description="Minimum content length"
    )
    max_length: Optional[int] = Field(
        default=None,
        description="Maximum content length"
    )

    def to_api_dict(self) -> dict:
        """Convert API search parameters to a dictionary for requests."""
        # Get non-None values from model
        values = {k: v for k, v in self.model_dump().items() if v is not None}
        return values


def screenpipe_search(
    content_type: Literal["OCR", "AUDIO", "ALL"],
    from_time: Optional[str] = None,
    to_time: Optional[str] = None,
    limit: Optional[int] = None,
    search_substring: Optional[str] = None,
    application: Optional[str] = None,
) -> dict:
    """Searches captured data stored in ScreenPipe's local database.

    Args:
        content_type: Type of screen/audio content to search for, default to ALL.
        from_time: ISO timestamp to filter results after this time.
        to_time: ISO timestamp to filter results before this time.
        limit: Maximum number of results to return.
        search_substring: Optional substring to filter text content.
        application: Optional filter to only show results from this application.
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
        assert kwargs == ScreenPipeAPISearch(
            **kwargs).to_api_dict(), "Bad search params!"
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
        processed = params

        # Validate limit
        if 'limit' in processed:
            original_limit = processed['limit']
            processed['limit'] = min(int(processed['limit']), MAX_SEARCH_LIMIT)
            if processed['limit'] != original_limit:
                logging.warning(
                    f"Limiting search results from {original_limit} to {processed['limit']}")

        # Capitalize app name if present
        if 'app_name' in processed and processed['app_name']:
            original_app = processed['app_name']
            processed['app_name'] = processed['app_name'].capitalize()
            if processed['app_name'] != original_app:
                logging.warning(
                    f"Capitalized app name from {original_app} to {processed['app_name']}")

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
        is_rejected = len(
            content) < reject_length and "thank you" in content.lower()
        return is_rejected

    @staticmethod
    def sanitize_results(results: dict,
                         replacement_tuples: List[Tuple[str, str]] = [],
                         offset_hours: Optional[float] = None) -> list[dict]:
        """Sanitize search results with improved error handling"""
        try:
            if not isinstance(results, dict) or "data" not in results:
                raise ValueError("Invalid results format")

            sanitized = []
            for result in results["data"]:
                sanitized_result = {
                    "timestamp": FilterUtils.format_timestamp(
                        result["content"]["timestamp"], offset_hours),
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


class ResponseUtils:
    """Utility methods for the Pipe class"""
    # TODO Add other response related methods here
    @staticmethod
    def form_final_user_message(
            user_message: str,
            sanitized_results: str,
            search_parameters: str) -> str:
        """
        Reformats the user message by adding context and rules from ScreenPipe search results.
        """
        assert isinstance(
            sanitized_results, str), "Sanitized results must be a string"
        assert isinstance(user_message, str), "User message must be a string"
        assert isinstance(
            search_parameters, str), "Search parameters must be a string"
        query = user_message
        context = sanitized_results
        search_params = search_parameters
        # TODO: Add the search parameters to the context
        reformatted_message = FINAL_RESPONSE_USER_MESSAGE.format(
            query=query, search_params=search_params, context=context)
        return reformatted_message

    @staticmethod
    def get_messages_with_screenpipe_data(
            user_message_string: str,
            search_results_list: List[dict],
            search_params_dict: dict) -> List[dict]:
        """
        Combines the last user message with sanitized ScreenPipe search results.
        """
        # TODO: Modify the results and search parameters into strings in this
        # function
        assert isinstance(
            user_message_string, str), "User message must be a string"
        assert isinstance(
            search_results_list, list), "Search results must be a list"
        assert isinstance(
            search_params_dict, dict), "Search parameters must be a dictionary"
        search_results_string = ResponseUtils.format_results_as_string(
            search_results_list)
        search_params_string = json.dumps(search_params_dict, indent=2)
        new_user_message = ResponseUtils.form_final_user_message(
            user_message_string, search_results_string, search_params_string)
        new_messages = [
            {"role": "system", "content": FINAL_RESPONSE_SYSTEM_MESSAGE},
            {"role": "user", "content": new_user_message}
        ]
        return new_messages

    @staticmethod
    def format_results_as_string(search_results: List[dict]) -> str:
        """Formats search results as a string"""
        response_string = ""
        for i, result in enumerate(search_results, 1):
            content = result.get("content", "").strip()
            result_type = result.get("type", "")
            metadata = {
                "device_name": result.get("device_name", ""),
                "app_name": result.get("app_name", ""),
                "timestamp": result.get("timestamp", "")
            }
            source_string = metadata['device_name'] or f"{metadata['app_name']}" or "N/A"
            result_string = (
                f"### Result {i} - {result_type.upper()}\n\n"
                f"{content}\n\n"
                f"**Source:** {source_string}  \n"
                f"**Timestamp:** {metadata['timestamp']}  \n"
                f"___\n\n"
            )
            response_string += result_string
        return response_string.strip()

def check_for_env_key(api_key: str) -> str:
    """Get API key from environment variable if prefixed with 'env.', otherwise return as-is"""
    env_reference_suffix = "env."
    if api_key[0:len(env_reference_suffix)] == env_reference_suffix:
        env_var = api_key[len(env_reference_suffix):]
        return os.getenv(env_var, api_key)
    return api_key
