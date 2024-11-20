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
from openai import OpenAI
from pydantic import BaseModel, Field

from ..utils.owui_utils.configuration import create_config
from ..utils.owui_utils.pipeline_utils import ResponseUtils, check_for_env_key

CONFIG = create_config()


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
            client,
            response_model: str,
            messages_with_screenpipe_data: List[dict],
            stream: bool):

        MAX_TOKENS = 3000
        if stream:
            return client.chat.completions.create(
                model=response_model,
                messages=messages_with_screenpipe_data,
                stream=True,
                max_tokens=MAX_TOKENS
            )
        else:
            final_response = client.chat.completions.create(
                model=response_model,
                messages=messages_with_screenpipe_data,
                max_tokens=MAX_TOKENS
            )
            return final_response.choices[0].message.content

    def is_pipe_body_valid(self, body: dict) -> bool:
        """Validates the structure and types of the pipe body dictionary.

        The pipe body must contain a user message and stream flag, with optional search data
        and error information.

        Args:
            body (dict): The pipe body to validate containing:
                - user_message_content (str): The user's message text
                - stream (bool): Whether to stream the response
                - inlet_error (str, optional): Any error from inlet processing
                - search_results (list, optional): List of search results
                - search_params (dict, optional): Search parameter settings
                - messages (list, optional): Message history

        Returns:
            bool: True if body has valid structure and types, False otherwise
        """
        if not isinstance(body, dict):
            return False
        # Validate mandatory user_message_content field
        if body.get("inlet_error") is not None:
            return isinstance(body["inlet_error"], str)
        # Validate required fields
        required_fields = {
            "user_message_content": str,
            "search_results": list,
            "search_params": dict,
        }
        for field, expected_type in required_fields.items():
            if not isinstance(body.get(field), expected_type):
                self.safe_log_error(
                    f"Required field {field} is missing or not of type {expected_type}",
                    ValueError)
                return False
        return True

    def pipe(self, body: dict) -> Union[str, Generator, Iterator]:
        """Main pipeline processing method"""
        if not self.is_pipe_body_valid(body):
            self.safe_log_error(
                f"Invalid! Check pipe request body", ValueError)
            return "Invalid pipe body!"
        if body["inlet_error"]:
            return body["inlet_error"]
        if self.valves.GET_RESPONSE:
            self._initialize_client()
        try:
            stream = body["stream"]
            user_message_string = body["user_message_content"]
            search_results_list = body["search_results"]
            search_params_dict = body["search_params"]
            # NOTE: Is it possible the values in body change between now and the outlet?
            if not self.valves.GET_RESPONSE:
                results_as_string = ResponseUtils.format_results_as_string(
                    search_results_list)
                return results_as_string

            messages_with_data = ResponseUtils.get_messages_with_screenpipe_data(
                user_message_string, search_results_list, search_params_dict)
            return self._generate_final_response(
                self.client, self.valves.RESPONSE_MODEL, messages_with_data, stream)
        except Exception as e:
            ERROR_LOGGING_ENABLED = False
            if ERROR_LOGGING_ENABLED:
                self.safe_log_error(str(e), e)
            else:
                self.safe_log_error("Error in pipe", e)
            return "An error occurred in the pipe."
