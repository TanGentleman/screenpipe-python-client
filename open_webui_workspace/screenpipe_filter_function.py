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
from utils.owui_utils.configuration import PipelineConfig
from utils.owui_utils.constants import EXAMPLE_SEARCH_JSON, JSON_SYSTEM_MESSAGE, TOOL_SYSTEM_MESSAGE
from utils.owui_utils.pipeline_utils import screenpipe_search, SearchParameters, PipeSearch, FilterUtils

try:
    from utils.baml_utils import construct_search_params
    ENABLE_BAML = True
except ImportError:
    ENABLE_BAML = False
    construct_search_params = None

class FilterBase:
    """Base class for Filter functionality"""

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
            default=False, description="Works best with gpt-4o-mini, use JSON for other models."
        )
        SCREENPIPE_SERVER_URL: str = Field(
            default="", description="URL for the ScreenPipe server"
        )

    def __init__(self):
        self.name = "screenpipe_pipeline"
        self.config = PipelineConfig.from_env()
        self.tools = [convert_to_openai_tool(screenpipe_search)]
        self.json_schema = SearchParameters.model_json_schema()
        self.replacement_tuples = self.config.replacement_tuples
        self.initialize_valves()

    def initialize_valves(self):
        """Initialize valve settings"""
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

class Filter(FilterBase):
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

    def _get_search_results_from_params(self, search_params: dict) -> dict | str:
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
            results =  construct_search_params(raw_query, current_iso_timestamp)
            if isinstance(results, str):
                return results
            search_params = results.model_dump()
            return self._get_search_results_from_params(search_params)

        system_message = self._get_system_message()
        messages = FilterUtils._prepare_initial_messages(messages, system_message)
        if self.native_tool_calling:
            return self._tool_response_as_results_or_str(messages)
        else:
            return self._json_response_as_results_or_str(messages)

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """Process incoming messages, performing search and sanitizing results."""
        body["inlet_error"] = None
        body["search_params"] = None
        body["search_results"] = None
        body["user_message_content"] = None
        original_messages = body.get("messages", [])
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
            body["search_results"] = sanitized_results

            # Store original user message
            last_message = original_messages[-1]
            assert last_message["role"] == "user"
            body["user_message_content"] = last_message["content"]

            # Append search params to user message
            search_params_as_string = json.dumps(self.search_params, indent=2)
            prologue = "Search parameters:"
            new_content = last_message["content"] + "\n\n" + prologue + "\n" + search_params_as_string
            last_message["content"] = new_content
        except Exception as e:
            self.safe_log_error("Error processing inlet", e)
            body["inlet_error"] = "Error in Filter inlet!"

        return body

    def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """Process outgoing messages, incorporating sanitized results if available."""
        try:
            messages = body.get("messages", [])
            message = messages[-1]
            if message.get("role") == "assistant":
                content = message.get("content", "")
                message["content"] = content + "\n\nOUTLET active."
            else:
                print("aaaah!")

        except Exception as e:
            self.safe_log_error("Error processing outlet", e)

        return body
