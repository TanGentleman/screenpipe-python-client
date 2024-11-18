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
from utils.owui_utils.constants import EXAMPLE_SEARCH_JSON, JSON_SYSTEM_MESSAGE, TOOL_SYSTEM_MESSAGE
from utils.owui_utils.pipeline_utils import screenpipe_search, SearchParameters, PipeSearch, FilterUtils


# Attempt to import BAML utils if enabled
use_baml = False
construct_search_params = None

if use_baml:
    try:
        from utils.baml_utils import baml_generate_search_params
        logging.info("BAML search parameter construction enabled")
    except ImportError:
        use_baml = False
        pass

ENABLE_BAML = use_baml

# Unpack the config
CONFIG = create_config()


class Filter:
    """Filter class for screenpipe functionality"""

    class Valves(BaseModel):
        """Valve settings for the Filter"""
        LLM_API_BASE_URL: str = Field(
            default=CONFIG.llm_api_base_url, description="Base URL for the LLM API"
        )
        LLM_API_KEY: str = Field(
            default=CONFIG.llm_api_key, description="API key for LLM access"
        )
        JSON_MODEL: Optional[str] = Field(
            default=CONFIG.json_model, description="Model to use for JSON calls"
        )
        TOOL_MODEL: str = Field(
            default=CONFIG.tool_model, description="Model to use for tool calls"
        )
        NATIVE_TOOL_CALLING: bool = Field(
            default=CONFIG.native_tool_calling,
            description="Works best with gpt-4o-mini, use JSON for other models."
        )
        SCREENPIPE_SERVER_URL: str = Field(
            default=CONFIG.screenpipe_server_url, description="URL for the ScreenPipe server"
        )

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
        current_time = FilterUtils.get_current_time()
        if self.valves.NATIVE_TOOL_CALLING:
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
        lm_studio_condition = self.valves.JSON_MODEL.startswith("lmstudio")
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
        print("Using json model:", self.valves.JSON_MODEL)
        try:
            response = self.client.chat.completions.create(
                model=self.valves.JSON_MODEL,
                messages=messages,
                response_format=self._get_json_response_format(),
            )
            response_text = response.choices[0].message.content
            if not response_text:
                return "No response generated."
            parsed_search_schema = FilterUtils.parse_schema_from_response(
                response_text, SearchParameters)
            if isinstance(parsed_search_schema, str):
                return response_text
            search_params = parsed_search_schema
            return self._get_search_results_from_params(search_params)
        except Exception:
            return "Failed json mode api call."

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
        if self.valves.NATIVE_TOOL_CALLING:
            return self._tool_response_as_results_or_str(messages)
        else:
            return self._json_response_as_results_or_str(messages)

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
        if not self.is_inlet_body_valid(body):
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
                print("Invalid outlet body!!")
                return body

            messages = body["messages"]
            # Restore original user message if available
            user_message_content = body.get("user_message_content")
            if user_message_content is not None:
                messages[-2]["content"] = user_message_content

            # Add search params to assistant message if available
            if self.search_params:
                content = messages[-1].get("content", "")
                pruned_params = {k: v for k, v in self.search_params.items() if v}
                params_str = json.dumps(pruned_params, indent=2)
                messages[-1]["content"] = f"{content}\n\nUsed search params:\n{params_str}"


        except Exception as e:
            self.safe_log_error("Error processing outlet", e)

        return body
