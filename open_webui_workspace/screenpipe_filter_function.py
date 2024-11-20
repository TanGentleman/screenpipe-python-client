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
from typing import Optional

# Third-party imports
from langchain_core.utils.function_calling import convert_to_openai_tool
from openai import OpenAI
from pydantic import BaseModel, Field

# Local imports
from utils.owui_utils.configuration import create_config
from utils.owui_utils.constants import TOOL_SYSTEM_MESSAGE
from utils.owui_utils.pipeline_utils import screenpipe_search, SearchParameters, PipeSearch, FilterUtils

# Unpack the config
CONFIG = create_config()
# Attempt to import BAML utils if enabled
use_baml = True

if use_baml:
    try:
        from utils.baml_utils import baml_generate_search_params
        logging.info("BAML search parameter construction enabled")
    except ImportError:
        use_baml = False
        pass

BAML_ENABLED = use_baml


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
        BAML_MODEL: Optional[str] = Field(
            default=CONFIG.baml_model,
            description="Model to use for BAML calls")
        TOOL_MODEL: str = Field(
            default=CONFIG.tool_model,
            description="Model to use for tool calls")
        NATIVE_TOOL_CALLING: bool = Field(
            default=CONFIG.native_tool_calling,
            description="Works best with gpt-4o-mini, use JSON for other models.")
        SCREENPIPE_SERVER_URL: str = Field(
            default=CONFIG.screenpipe_server_url,
            description="URL for the ScreenPipe server")

    def __init__(self):
        self.name = "screenpipe_pipeline"
        self.tools = [convert_to_openai_tool(screenpipe_search)]
        self.json_schema = SearchParameters.model_json_schema()
        self.replacement_tuples = CONFIG.replacement_tuples
        self.valves = self.Valves()
        self.client = None
        self.searcher = None
        self.search_params = None

    def set_valves(self, valves: Optional[dict] = None):
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
        self.client = OpenAI(
            base_url=self.valves.LLM_API_BASE_URL,
            api_key=self.valves.LLM_API_KEY
        )

    def _initialize_searcher(self):
        """Initialize PipeSearch instance"""
        self.searcher = PipeSearch(
            {"screenpipe_server_url": self.valves.SCREENPIPE_SERVER_URL}
        )
        self.search_params = None

    def _get_system_message(self) -> str:
        """Get appropriate system message based on configuration"""
        if self.valves.NATIVE_TOOL_CALLING:
            return TOOL_SYSTEM_MESSAGE
        else:
            raise ValueError(
                "Native tool calling must be enabled for System Message!")

    def _tool_response_as_results_or_str(self, messages: list) -> str | dict:
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
        # Can be a string or search_results dicts
        return results

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
        try:
            # Create and validate search parameters object
            search_param_object = SearchParameters(**search_params)
            # self.safe_log_error(f"Search params: {search_param_object}", None)

            # Store search parameters for later reference
            self.search_params = search_param_object.to_dict()
            # Convert to API-compatible format and execute search
            api_params = search_param_object.to_api_dict()
            search_results = self.searcher.search(**api_params)
        except Exception as e:
            self.safe_log_error("Error unpacking SearchParameters object!", e)
            raise ValueError
        if not search_results:
            return "No results found"
        if "error" in search_results:
            return search_results["error"]
        return search_results

    def _make_tool_api_call(self, messages):
        print("Using tool model:", self.valves.TOOL_MODEL)
        return self.client.chat.completions.create(
            model=self.valves.TOOL_MODEL,
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

    def _baml_response_as_results_or_str(self, messages: list) -> str | dict:
        if not BAML_ENABLED:
            self.safe_log_error("BAML is not enabled!", ValueError)
            raise ValueError
        user_message = messages[-1]["content"]
        current_iso_timestamp = FilterUtils.get_current_time()
        parsed_response = baml_generate_search_params(
            user_message, current_iso_timestamp)
        if isinstance(parsed_response, str):
            print(f"WARNING: BAML error!")
            return parsed_response

        def fix_baml_response(baml_search_params) -> dict:
            search_params = baml_search_params.model_dump()
            search_params["content_type"] = search_params["content_type"].value
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
        return self._get_search_results_from_params(search_params)

    def _get_search_results(self, messages: list[dict]) -> str | dict:
        if self.valves.NATIVE_TOOL_CALLING:
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
        if not isinstance(body, dict):
            return False
        messages = body.get("messages", [])
        if not messages:
            return False
        if messages[-1].get("role") != "user":
            return False
        return True

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """Process incoming messages, performing search and sanitizing results."""
        print(f"inlet:{__name__}")
        # print(f"inlet:body:{body}")
        print(f"inlet:user:{__user__}")
        body["inlet_error"] = None
        body["user_message_content"] = None
        body["search_params"] = None
        body["search_results"] = None
        if not self.is_inlet_body_valid(body):
            body["inlet_error"] = "Invalid inlet body"
            return body
        original_messages = body["messages"]
        body["user_message_content"] = original_messages[-1]["content"]
        try:
            # Initialize settings and prepare messages
            self.initialize_settings()
            raw_results = self._get_search_results(original_messages)
            if not raw_results:
                body["inlet_error"] = "No results found"
                return body
            # Handle error case
            if isinstance(raw_results, str):
                body["inlet_error"] = raw_results
                return body

            assert self.search_params is not None
            # Store search params
            body["search_params"] = self.search_params

            # Sanitize and store results
            search_results = FilterUtils.sanitize_results(
                raw_results, self.replacement_tuples)

            if not search_results:
                body["inlet_error"] = "No sanitized results found"
                return body

            body["search_results"] = search_results
            # Store original user message
            REPLACE_USER_MESSAGE = False
            if REPLACE_USER_MESSAGE:
                # NOTE: This REPLACES the user message in the body dictionary

                # Append search params to user message
                search_params_as_string = json.dumps(
                    self.search_params, indent=2)
                prologue = "Search parameters:"
                refactored_last_message = original_messages[-1]["content"] + \
                    "\n\n" + prologue + "\n" + search_params_as_string
                original_messages[-1]["content"] = refactored_last_message
        except Exception as e:
            self.safe_log_error("Error processing inlet", e)
            body["inlet_error"] = "Error in Filter inlet!"

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
        print(f"outlet:user:{__user__}")
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
                # Get current content and search results
                assistant_content = messages[-1].get("content", "")
                search_results = body.get("search_results")
                if not search_results:
                    result_count = 0
                else:
                    result_count = len(search_results)

                # Format search parameters as pretty JSON
                formatted_params = json.dumps(self.search_params, indent=2)

                # Build summary message
                summary = f"\n\nFound {result_count} results with search params:\n{formatted_params}"

                # Update assistant message with original content plus summary
                messages[-1]["content"] = assistant_content + summary

        except Exception as e:
            self.safe_log_error("Error processing outlet", e)

        return body
