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
from utils.configuration import PipelineConfig
from utils.constants import EXAMPLE_SEARCH_JSON, JSON_SYSTEM_MESSAGE, TOOL_SYSTEM_MESSAGE
from utils.pipeline_utils import screenpipe_search, SearchParameters, PipeSearch, FilterUtils

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
        GET_RESPONSE: bool = Field(
            default=False, description="Whether to get a response from the pipe"
        )
        RESPONSE_MODEL: str = Field(
            default="", description="Model to use for response"
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
                "GET_RESPONSE": self.config.get_response,
                "RESPONSE_MODEL": self.config.response_model
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
        self.get_response = self.valves.GET_RESPONSE

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
        self.response_model = self.valves.RESPONSE_MODEL or self.config.response_model
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
            parsed_search_schema = FilterUtils.parse_schema_from_response(
                response_text, SearchParameters)
            if isinstance(parsed_search_schema, str):
                return response_text

            function_args = parsed_search_schema
            self.search_params = function_args
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
                self.search_params = function_args
                print("Constructed search params:", function_args)
                search_results = self.searcher.search(**function_args)
                if not search_results:
                    return "No results found"
                if "error" in search_results:
                    return search_results["error"]
                return search_results
        raise ValueError("No valid tool call found")

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
            system_message = self._get_system_message()
            messages = FilterUtils._prepare_initial_messages(original_messages, system_message)
            # Get search results
            results = (self._tool_response_as_results_or_str(messages)
                       if self.native_tool_calling
                       else self._json_response_as_results_or_str(messages))
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
