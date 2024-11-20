"""
title: Screenpipe Pipe
author: TanGentleman
author_url: https://github.com/TanGentleman
funding_url: https://github.com/TanGentleman
version: 0.5
"""

import json
from typing import Optional, Union, Generator, Iterator, List
import logging
from openai import OpenAI, Stream
from openai.types.chat import ChatCompletionChunk, ChatCompletion

from pydantic import BaseModel, Field

from ..utils.owui_utils.configuration import create_config
from ..utils.owui_utils.pipeline_utils import ResponseUtils, check_for_env_key

CONFIG = create_config()

MAX_RESPONSE_TOKENS = 3000

class Pipe():
    """Pipe class for screenpipe functionality"""
    class Valves(BaseModel):
        """Valve settings for the Pipe"""
        GET_RESPONSE: bool = Field(
            default=CONFIG.get_response,
            description="Whether to get a response from the pipe")
        RESPONSE_MODEL: str = Field(
            default=CONFIG.response_model,
            description="Model to use for response")
        LLM_API_BASE_URL: str = Field(
            default=CONFIG.llm_api_base_url,
            description="Base URL for the OpenAI API")
        LLM_API_KEY: str = Field(
            default=CONFIG.llm_api_key,
            description="API key for the OpenAI API")

    def __init__(self):
        self.type = "pipe"
        self.name = "screenpipe_pipeline"
        self.valves = self.Valves()
        self.client = None

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

    def _initialize_client(self):
        """Initialize OpenAI client"""
        self.client = OpenAI(
            base_url=self.valves.LLM_API_BASE_URL,
            api_key=check_for_env_key(self.valves.LLM_API_KEY)
        )

    def safe_log_error(self, message: str, error: Exception) -> None:
        """Safely log an error without potentially exposing PII."""
        error_type = type(error).__name__
        logging.error(f"{message}: {error_type}")

    def _generate_final_response(
            self,
            messages_with_screenpipe_data: List[dict],
            stream: bool) -> Union[Stream[ChatCompletionChunk], ChatCompletion]:

        client = self.client
        response_model = self.valves.RESPONSE_MODEL
        assert client is not None
        if stream:
            response: Stream[ChatCompletionChunk] = client.chat.completions.create(
                model=response_model,
                messages=messages_with_screenpipe_data,
                stream=True,
                max_tokens=MAX_RESPONSE_TOKENS
            )
            return response
        else:
            final_response: ChatCompletion = client.chat.completions.create(
                model=response_model,
                messages=messages_with_screenpipe_data,
                max_tokens=MAX_RESPONSE_TOKENS
            )
            return final_response.choices[0].message.content

    def is_pipe_body_valid(self, body: dict) -> bool:
        """Validates the structure and types of the pipe body dictionary.

        Args:
            body (dict): The pipe body containing:
                - user_message_content (str, required): User's message text
                - stream (bool, required): Whether to stream the response
                - inlet_error (str, optional): Error from inlet processing
                - search_results (list, required): List of search results
                - search_params (dict, required): Search parameter settings

        Returns:
            bool: True if body has valid structure and types
        """
        if not isinstance(body, dict):
            self.safe_log_error("Body must be a dictionary", TypeError)
            return False

        # Early return if inlet_error exists and is valid
        if body.get("inlet_error"):
            if not isinstance(body["inlet_error"], str):
                self.safe_log_error("inlet_error must be a string", TypeError)
                return False
            return True

        # Validate all required fields
        required_fields = {
            "user_message_content": str,
            "stream": bool,
            "search_results": list,
            "search_params": dict,
        }
        
        for field, expected_type in required_fields.items():
            if field not in body:
                self.safe_log_error(f"Missing required field: {field}", ValueError)
                return False
            if not isinstance(body[field], expected_type):
                self.safe_log_error(
                    f"Field {field} must be of type {expected_type.__name__}", TypeError)
                return False
                
        return True

    def pipe(self, body: dict) -> Union[str, Generator, Iterator]:
        """Process the pipeline request.
        
        Args:
            body (dict): The validated request body
            
        Returns:
            Union[str, Generator, Iterator]: Response string or stream
        """
        print(f"inlet:{__name__}")
        if not self.is_pipe_body_valid(body):
            return "Invalid pipe body!"

        if body.get("inlet_error"):
            return body["inlet_error"]

        try:
            # Extract required fields
            stream = body["stream"]
            user_message = body["user_message_content"]
            search_results = body["search_results"]
            search_params = body["search_params"]
            
            # Return early if response not needed
            if not self.valves.GET_RESPONSE:
                return ResponseUtils.format_results_as_string(search_results)

            # Initialize client and generate response
            self._initialize_client()
            
            messages = ResponseUtils.get_messages_with_screenpipe_data(
                user_message, search_results, search_params)
            
            return self._generate_final_response(
                messages, 
                stream
            )


        except Exception as e:
            ERROR_LOGGING_ENABLED = False
            if ERROR_LOGGING_ENABLED:
                self.safe_log_error(str(e), e)
            else:
                self.safe_log_error("Error in pipe", e)
            return f"An error occurred in the pipe. {str(e)}"
