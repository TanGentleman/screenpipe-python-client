"""
title: Screenpipe Pipe (Full)
author: TanGentleman
author_url: https://github.com/TanGentleman
funding_url: https://github.com/TanGentleman
version: 0.1
"""

from typing import Union, Generator, Iterator, List
import logging
from openai import OpenAI
from pydantic import BaseModel, Field

### from utils.owui_utils.configuration import PipelineConfig
import os
from dataclasses import dataclass
from typing import List, Tuple

# NOTE: Base URL and API key can be set in the environment variables file
# Alternatively, they can be set as Valves in the UI

SENSITIVE_KEY = os.getenv('LLM_API_KEY', '')
if not SENSITIVE_KEY:
    print("WARNING: LLM_API_KEY environment variable is not set!")
    # raise ValueError("LLM_API_KEY environment variable is not set!")
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
GET_RESPONSE = False

# NOTE: If NATIVE_TOOL_CALLING is True, tool model is used instead of the json model

# Model Configuration
DEFAULT_TOOL_MODEL = "Llama-3.1-70B"
DEFAULT_JSON_MODEL = "sambanova-llama-8b"
DEFAULT_RESPONSE_MODEL = "sambanova-llama-8b"

# NOTE: Model name must be valid for the endpoint:
# {DEFAULT_LLM_API_BASE_URL}/v1/chat/completions

# Time Configuration
PREFER_24_HOUR_FORMAT = True
DEFAULT_UTC_OFFSET = -7  # PDT

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
    get_response: bool
    response_model: str

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
            get_response=get_bool_env('GET_RESPONSE', GET_RESPONSE),
            response_model=os.getenv('RESPONSE_MODEL', DEFAULT_RESPONSE_MODEL),
            
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

### from utils.owui_utils.constants import ALT_FINAL_RESPONSE_SYSTEM_MESSAGE
ALT_FINAL_RESPONSE_SYSTEM_MESSAGE = """You analyze all types of data from screen recordings and audio transcriptions. The user's query is designed to filter the search results. Provide comprehensive insights of the provided data."""

class ResponseUtils:
    """Utility methods for the Pipe class"""
    # TODO Add other response related methods here
    @staticmethod
    def form_final_user_message(
            user_message: str,
            sanitized_results: str) -> str:
        """
        Reformats the user message by adding context and rules from ScreenPipe search results.
        """
        assert isinstance(
            sanitized_results, str), "Sanitized results must be a string"
        assert isinstance(user_message, str), "User message must be a string"
        query = user_message
        context = sanitized_results

        reformatted_message = f"""You are given context from personal screen and microphone data, as well as a user query, given inside xml tags. Even if the query is not relevant to the context, describe the context in detail.
<context>
{context}
</context>

<user_query>
{query}
</user_query>"""
        return reformatted_message

    @staticmethod
    def get_messages_with_screenpipe_data(
            messages: List[dict],
            results_as_string: str) -> List[dict]:
        """
        Combines the last user message with sanitized ScreenPipe search results.
        """
        if messages[-1]["role"] != "user":
            raise ValueError("Last message must be from the user!")
        if len(messages) > 2:
            print("Warning! This LLM call does not use past chat history!")
        
        assert isinstance(messages[-1]["content"], str), "User message must be a string"
        new_user_message = ResponseUtils.form_final_user_message(
            messages[-1]["content"], results_as_string)
        new_messages = [
            {"role": "system", "content": ALT_FINAL_RESPONSE_SYSTEM_MESSAGE},
            {"role": "user", "content": new_user_message}
        ]
        return new_messages
    
class Pipe():
    """Pipe class for screenpipe functionality"""
    class Valves(BaseModel):
        """Valve settings for the Pipe"""
        GET_RESPONSE: bool = Field(
            default=False, description="Whether to get a response from the pipe"
        ) # NOTE: Default of False takes precedence over config default for get_response
        RESPONSE_MODEL: str = Field(
            default="", description="Model to use for response"
        )
        LLM_API_BASE_URL: str = Field(
            default="", description="Base URL for the OpenAI API"
        )
        LLM_API_KEY: str = Field(
            default="", description="API key for the OpenAI API"
        )
    def __init__(self):
        self.type = "pipe"
        self.name = "screenpipe_pipeline"
        self.config = PipelineConfig.from_env()
        self.valves = self.Valves(
            **{
                "LLM_API_BASE_URL": self.config.llm_api_base_url,
                "LLM_API_KEY": self.config.llm_api_key,
                "GET_RESPONSE": self.config.get_response,
                "RESPONSE_MODEL": self.config.response_model
            }
        )
        
    def _initialize_client(self):
        """Initialize OpenAI client"""
        base_url = self.valves.LLM_API_BASE_URL or self.config.llm_api_base_url
        api_key = self.valves.LLM_API_KEY or self.config.llm_api_key
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        self.get_response = self.valves.GET_RESPONSE
        self.response_model = self.valves.RESPONSE_MODEL or self.config.response_model

    def safe_log_error(self, message: str, error: Exception) -> None:
        """Safely log an error without potentially exposing PII."""
        error_type = type(error).__name__
        logging.error(f"{message}: {error_type}")
    
    def _generate_final_response(self, client, response_model: str, messages_with_screenpipe_data: List[dict], stream: bool):
        if stream:
            return client.chat.completions.create(
                model=response_model,
                messages=messages_with_screenpipe_data,
                stream=True
            )
        else:
            final_response = client.chat.completions.create(
                model=response_model,
                messages=messages_with_screenpipe_data,
            )
            return final_response.choices[0].message.content

    def pipe(self, body: dict) -> Union[str, Generator, Iterator]:
        """Main pipeline processing method"""
        if self.valves.GET_RESPONSE:
            self._initialize_client()
            assert self.get_response is True
        else:
            self.get_response = False
        stream = body["stream"]
        messages = body["messages"]
        try:
            if body["inlet_error"]:
                return body["inlet_error"]
            
            search_results = body.get("search_results", [])
            assert search_results
            search_results_as_string = str(search_results)

            if self.get_response:
                messages_with_data = ResponseUtils.get_messages_with_screenpipe_data(
                    messages,
                    search_results_as_string
                )
                return self._generate_final_response(self.client, self.response_model, messages_with_data, stream)
            
            epilogue = ""
            return search_results_as_string + epilogue
        except Exception as e:
            print(str(e))
            self.safe_log_error("Error in pipe", e)
            return "An error occurred in the pipe."
            