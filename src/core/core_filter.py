"""
title: Screenpipe Filter
author: TanGentleman
author_url: https://github.com/TanGentleman
funding_url: https://github.com/TanGentleman
version: 0.4
"""

### 1. IMPORTS ###
# Standard library imports
import logging
import json
import os
from typing import Optional

# Third-party imports
from langchain_core.utils.function_calling import convert_to_openai_tool
from openai import OpenAI
from openai.types.chat import ChatCompletion
from pydantic import BaseModel, Field

# Local imports
from ..utils.owui_utils.configuration import create_config
from ..utils.constants import TOOL_SYSTEM_MESSAGE
from ..utils.owui_utils.pipeline_utils import ResponseUtils, check_for_env_key, screenpipe_search, SearchParameters, PipeSearch, FilterUtils

# Unpack the config
CONFIG = create_config()
# Attempt to import BAML utils if enabled

try:
    from ..utils.baml_utils import baml_generate_search_params, BamlConfig
    logging.info("BAML search parameter construction enabled")
    use_baml = True
except ImportError:
    use_baml = False
    pass

BAML_ENABLED = use_baml

INLET_ADJUSTS_USER_MESSAGE = False

### 2. ERROR CLASSES ###
class CoreError(Exception):
    """Base class for core pipeline errors"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class InvalidBodyError(CoreError):
    """Raised when the request body is invalid"""
    pass

class EmptySearchError(CoreError):
    """Raised when no search results are found"""
    pass

class SearchError(CoreError):
    """Raised when there's an error during search execution"""
    pass

class ConfigurationError(CoreError):
    """Raised when there's an error in pipeline configuration"""
    pass

class ToolCallError(CoreError):
    """Raised when there's an error processing tool calls"""
    pass

class BAMLError(CoreError):
    """Raised when there's an error in BAML processing"""
    pass

class Filter:
    """Filter class for screenpipe functionality"""

    class Valves(BaseModel):
        """Valve settings for the Filter"""
        LLM_API_BASE_URL: str = Field(
            default=CONFIG.llm_api_base_url,
            description="Base URL for the LLM API")
        LLM_API_KEY: str = Field(
            default=CONFIG.llm_api_key, description="API key for LLM access"
        )
        FILTER_MODEL: Optional[str] = Field(
            default=CONFIG.filter_model,
            description="Model to use for BAML calls")
        FORCE_TOOL_CALLING: bool = Field(
            default=CONFIG.force_tool_calling,
            description="Works best with gpt-4o-mini, use JSON for other models.")
        SCREENPIPE_SERVER_URL: str = Field(
            default=CONFIG.screenpipe_server_url,
            description="URL for the ScreenPipe server")

    def __init__(self):
        self.name = "screenpipe_pipeline"
        self.tools = [convert_to_openai_tool(screenpipe_search)]
        self.replacement_tuples = CONFIG.replacement_tuples or []
        self.offset_hours = CONFIG.default_utc_offset or 0
        self.valves = self.Valves()
        self.client = None
        self.searcher = None
        self.search_params = None
        self.search_results = None
        # NOTE: The convert_to_openai_tool should have strict=True, but error
        # is handled differently.

    # NOTE: Should this return anything?
    def set_valves(self, valves: Optional[dict] = None) -> None:
        """Update valve settings from a dictionary of values"""
        if valves is None:
            self.valves = self.Valves()
            return
        assert self.valves is not None
        for key, value in valves.items():
            if hasattr(self.valves, key):
                # TODO: Validate value type
                setattr(self.valves, key, value)
            else:
                print(f"Invalid valve: {key}")

    def safe_log_error(self, message: str, error: Exception) -> None:
        """Safely log an error without potentially exposing PII."""
        error_type = type(error).__name__
        logging.error(f"{message}: {error_type}")

    def initialize_settings(self):
        """Initialize all pipeline settings"""
        self._initialize_client()
        self._initialize_searcher()

    def _initialize_client(self):
        """Initialize OpenAI client"""
        api_key = check_for_env_key(self.valves.LLM_API_KEY)
        base_url = self.valves.LLM_API_BASE_URL
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )

    def _initialize_searcher(self):
        """Initialize PipeSearch instance"""
        self.searcher = PipeSearch(
            {"screenpipe_server_url": self.valves.SCREENPIPE_SERVER_URL}
        )
        self.search_params = None
        self.search_results = None

    def _tool_response_as_results_or_str(
            self, messages: list[dict]) -> str | dict:
        """Process messages using tool-based approach and return search results.

        Args:
            messages: List of message dictionaries containing role and content

        Returns:
            dict: Search results if successful
            str: Error message if processing fails
        """
        # Refactor user message
        user_message = messages[-1]["content"]
        current_iso_timestamp = FilterUtils.get_current_time()
        new_user_message = f"USER MESSAGE: {user_message}\n(CURRENT TIME: {current_iso_timestamp})"
        system_message = TOOL_SYSTEM_MESSAGE
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": new_user_message}
        ]
        try:
            response = self._make_tool_api_call(messages)
            # Extract tool calls
            tool_calls = response.choices[0].message.model_dump().get(
                'tool_calls', [])
        except Exception:
            raise ToolCallError("Failed tool api call.")

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
        try:
            results = self._process_tool_calls(tool_calls)
        except Exception:
            raise ToolCallError(f"Error processing tool calls.")
        # Can be a string or search_results dicts
        return results

    def _get_search_results_from_params(
            self, search_params: dict) -> dict | str:
        """Execute search using provided parameters and return results.
        
        Args:
            search_params: Dictionary containing search parameters
            
        Returns:
            dict: Search results if successful
            str: Error message if search fails
            
        Raises:
            SearchError: If search parameters are invalid or search fails
        """
        # Validate and convert search parameters
        try:
            search_param_object = SearchParameters(**search_params)
            self.search_params = search_param_object.to_dict()
            api_params = search_param_object.to_api_dict()
        except ValueError as e:
            self.safe_log_error("Invalid search parameters", e)
            raise SearchError("Invalid search parameters.")

        # Execute search
        try:
            search_results = self.searcher.search(**api_params)
        except Exception as e:
            self.safe_log_error("Error during search execution", e)
            raise SearchError("Error executing search")

        # Validate search results
        if not search_results:
            raise EmptySearchError("No results found")
        if "search_error" in search_results:
            raise SearchError(search_results["search_error"])

        return search_results

    def _make_tool_api_call(self, messages) -> ChatCompletion:
        print("Using tool model:", self.valves.FILTER_MODEL)
        response: ChatCompletion = self.client.chat.completions.create(
            model=self.valves.FILTER_MODEL,
            messages=messages,
            tools=self.tools,
            tool_choice="auto",
            stream=False
        )
        return response

    def _process_tool_calls(self, tool_calls: list[dict]) -> dict | str:
        """Process tool calls and return results"""
        for tool_call in tool_calls:
            if tool_call['function']['name'] == 'screenpipe_search':
                function_args = json.loads(tool_call['function']['arguments'])
                search_params = function_args
                try:
                    return self._get_search_results_from_params(search_params)
                except SearchError as e:
                    raise e
        raise ValueError("No valid tool call found")

    def _baml_response_as_results_or_str(self, messages: list) -> str | dict:
        if not BAML_ENABLED:
            self.safe_log_error("BAML is not enabled!", ValueError)
            raise ValueError
        user_message = messages[-1]["content"]
        current_iso_timestamp = FilterUtils.get_current_time()
        baml_config = BamlConfig(
            model=self.valves.FILTER_MODEL,
            base_url=self.valves.LLM_API_BASE_URL,
            api_key=self.valves.LLM_API_KEY
        )
        parsed_response = baml_generate_search_params(
            user_message, current_iso_timestamp, baml_config)
        if isinstance(parsed_response, str):
            print(f"WARNING: BAML error!")
            return parsed_response

        def fix_baml_response(baml_search_params) -> dict:
            search_params = baml_search_params.model_dump()
            if search_params.get("time_range"):
                time_range = search_params["time_range"]
                search_params["from_time"] = time_range["from_time"]
                search_params["to_time"] = time_range["to_time"]

            fixed_search_params = SearchParameters(**search_params).to_dict()
            return fixed_search_params
        try:
            search_params = fix_baml_response(parsed_response)
        except Exception as e:
            self.safe_log_error("Error fixing BAML search params!", e)
            raise ValueError
        try:
            return self._get_search_results_from_params(search_params)
        except SearchError as e:
            return e.message

    def _get_search_results(self, messages: list[dict]) -> str | dict:
        if self.valves.FORCE_TOOL_CALLING:
            return self._tool_response_as_results_or_str(messages)
        else:
            assert BAML_ENABLED, "BAML is not enabled! Enable it or try native tool calling instead."
            return self._baml_response_as_results_or_str(messages)

    def is_inlet_body_valid(self, body: dict) -> bool:
        """Validates the structure and types of the inlet body dictionary.

        Args:
            body: Dictionary containing messages

        Returns:
            bool: True if body has valid structure and types, False otherwise

        The body must contain:
        - messages list with at least 1 message
        - Last message from user
        """
        if not BAML_ENABLED:
            if not self.valves.FORCE_TOOL_CALLING:
                self.safe_log_error(
                    "BAML and Tool calling are both disabled!", ValueError)
                return False
        if not isinstance(body, dict):
            return False
        messages = body.get("messages", [])
        if not messages:
            return False
        if messages[-1].get("role") != "user":
            return False
        return True

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """Process incoming messages, performing search and sanitizing results.

        Args:
            body: Dictionary containing messages and other request data
            __user__: Optional user information dictionary

        Returns:
            dict: Processed body with search results and any error messages

        The function will add the following keys to the body:
        - inlet_error: Error message if any
        - user_message_content: Original user message
        - search_params: Parameters used for search
        - search_results: Sanitized search results
        """
        print(f"inlet:{__name__}")
        # print(f"inlet:body:{body}")
        # print(f"inlet:user:{__user__}")
        body["inlet_error"] = None
        body["core_error"] = None
        body["user_message_content"] = None
        body["search_params"] = None
        body["search_results"] = None
        if not self.is_inlet_body_valid(body):
            raise InvalidBodyError("Invalid inlet body")
        original_messages = body["messages"]
        body["user_message_content"] = original_messages[-1]["content"]
        try:
            # Initialize settings and prepare messages
            self.initialize_settings()
            raw_results = self._get_search_results(original_messages)

            if isinstance(raw_results, str):
                raise SearchError(raw_results)

            assert self.search_params is not None
            body["search_params"] = self.search_params

            if not raw_results.get("data", []):
                raise EmptySearchError("No results found")

            # Sanitize and store results
            search_results_list = FilterUtils.sanitize_results(
                raw_results, self.replacement_tuples, self.offset_hours)

            if not search_results_list:
                raise SearchError("No search results. (Some were rejected!)")

            body["search_results"] = search_results_list
            self.search_results = search_results_list
            # Store original user message
            if INLET_ADJUSTS_USER_MESSAGE:
                # NOTE: This REPLACES the user message in the body dictionary
                # Append search params to user message
                search_params_as_string = json.dumps(
                    self.search_params, indent=2)
                prologue = "Search parameters:"
                refactored_last_message = original_messages[-1]["content"] + \
                    "\n\n" + prologue + "\n" + search_params_as_string
                original_messages[-1]["content"] = refactored_last_message
        except CoreError as e:
            self.safe_log_error(f"Core error in inlet: {e.message}", e)
            body["core_error"] = e.message
            body["inlet_error"] = e.message
        except Exception as e:
            # self.safe_log_error(f"{e}", None)
            self.safe_log_error("Unexpected error in inlet", e)
            body["core_error"] = "Unexpected error in Filter inlet"
            body["inlet_error"] = "Unexpected error in Filter inlet"
        return body

    def is_outlet_body_valid(self, body: dict) -> bool:
        """Validates the structure and types of the outlet body dictionary.

        Args:
            body: Dictionary containing messages

        Returns:
            bool: True if body has valid structure and types, False otherwise

        The body must contain:
        - messages list with at least 2 messages
        - Last message from user, second-to-last from assistant
        """
        if not isinstance(body, dict):
            return False

        messages = body.get("messages", [])
        if not messages or len(messages) < 2:
            return False

        if (messages[-1].get("role") != "assistant" or
                messages[-2].get("role") != "user"):
            return False

        return True

    def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """Process outgoing messages."""
        print(f"outlet:{__name__}")
        # print(f"outlet:body:{body}")
        # print(f"outlet:user:{__user__}")
        try:
            if not self.is_outlet_body_valid(body):
                self.safe_log_error("Invalid outlet body!!", ValueError)
                return body

            messages = body["messages"]

            # Restore original user message if available
            user_message_content = body.get("user_message_content")
            # TODO: Add any useful information to the user message
            if user_message_content is not None:
                # + "\n(Outlet active.)"
                messages[-2]["content"] = user_message_content

            # Append search parameters and result count to assistant's response
            # if available
            if self.search_params:
                assistant_content = messages[-1].get("content", "")
                search_results = self.search_results
                result_count = 0
                results_as_string = ""
                if search_results:
                    result_count = len(search_results)
                    results_as_string = ResponseUtils.format_results_as_string(
                        search_results)
                # Format search parameters as pretty JSON
                formatted_params = json.dumps(self.search_params, indent=2)

                # Build summary message
                summary = f"\n\nUsed {result_count} results with search params:\n{formatted_params}"

                # Update assistant message with original content plus summary
                final_content = results_as_string + "\n\n" + assistant_content + summary
                messages[-1]["content"] = final_content.strip()

        except Exception as e:
            # self.safe_log_error(f"{e}", None)
            self.safe_log_error("Error processing outlet", e)

        return body
