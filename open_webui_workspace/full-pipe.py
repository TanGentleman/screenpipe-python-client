"""
title: Screenpipe Pipe (Full)
author: TanGentleman
author_url: https://github.com/TanGentleman
funding_url: https://github.com/TanGentleman
version: 0.2
"""
import json
from typing import Union, Generator, Iterator, List
import logging
from openai import OpenAI
from pydantic import BaseModel, Field

# from utils.owui_utils.configuration import PipelineConfig
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

# from utils.owui_utils.pipeline_utils import ResponseUtils
FINAL_RESPONSE_SYSTEM_MESSAGE = """You are a helpful AI assistant analyzing personal data from ScreenPipe. Your task is to:

1. Understand the user's intent from their original query and the search parameters they constructed
2. Carefully analyze the provided context (audio/OCR data) based on those search parameters
3. Give clear, relevant insights that directly address the user's query
4. If the context seems less relevant to the query, explain why and still extract any useful information
5. Be mindful that you are handling personal data and maintain appropriate discretion

The data will be provided in XML tags:
- <user_query>: The original user question
- <search_parameters>: The parameters used to filter the data
- <context>: The actual personal data chunks to analyze

Focus on making connections between the user's intent and the retrieved data to provide meaningful analysis."""
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
        assert isinstance(search_parameters, str), "Search parameters must be a string"
        query = user_message
        context = sanitized_results
        search_params = search_parameters
        #TODO: Add the search parameters to the context
        reformatted_message = f"""Use the context from my personal data to answer as best as possible. Results have been filtered by the search parameters. Analyze the context, even if the query is less relevant.
<user_query>
{query}
</user_query>

<search_parameters>
{search_params}
</search_parameters>

<context>
{context}
</context>"""
        return reformatted_message

    @staticmethod
    def get_messages_with_screenpipe_data(
            messages: List[dict],
            results_as_string: str,
            search_parameters: str) -> List[dict]:
        """
        Combines the last user message with sanitized ScreenPipe search results.
        """
        if messages[-1]["role"] != "user":
            raise ValueError("Last message must be from the user!")
        if len(messages) > 2:
            print("Warning! This LLM call does not use past chat history!")

        assert isinstance(messages[-1]["content"],
                          str), "User message must be a string"
        original_user_message = messages[-1]["content"]
        new_user_message = ResponseUtils.form_final_user_message(
            original_user_message, results_as_string, search_parameters)
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
            content = result["content"].strip()
            result_type = result["type"]
            metadata = {
                "device_name": result.get("device_name", ""),
                "timestamp": result.get("timestamp", "")
            }
            result_string = (
                f"=== CHUNK {i}: {result_type.upper()} CONTENT ===\n"
                f"{content}\n"
                f"=== METADATA ===\n"
                f"Device: {metadata['device_name']}\n"
                f"Time: {metadata['timestamp']}\n"
                f"==================\n\n"
            )
            response_string += result_string
        return response_string.strip()

class Pipe():
    """Pipe class for screenpipe functionality"""
    class Valves(BaseModel):
        """Valve settings for the Pipe"""
        GET_RESPONSE: bool = Field(
            default=False, description="Whether to get a response from the pipe"
        )  # NOTE: Default of False takes precedence over config default for get_response
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

    def _generate_final_response(
            self,
            client,
            response_model: str,
            messages_with_screenpipe_data: List[dict],
            stream: bool):
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
            
            search_results = body["search_results"]
            assert search_results is not None
            search_results_as_string = ResponseUtils.format_results_as_string(search_results)
            search_params_dict = body["search_params"]
            assert search_params_dict is not None
            search_params = json.dumps(search_params_dict)
            if self.get_response:
                messages_with_data = ResponseUtils.get_messages_with_screenpipe_data(
                    messages, search_results_as_string, search_params)
                return self._generate_final_response(
                    self.client, self.response_model, messages_with_data, stream)

            epilogue = ""
            return search_results_as_string + epilogue
        except Exception as e:
            self.safe_log_error("Error in pipe", e)
            return "An error occurred in the pipe."
