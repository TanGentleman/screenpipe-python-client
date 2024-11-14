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
