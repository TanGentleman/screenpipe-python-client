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

from utils.owui_utils.configuration import create_config
from utils.owui_utils.pipeline_utils import ResponseUtils

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
            api_key=self.valves.LLM_API_KEY
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

    def is_pipe_body_valid(self, body: dict) -> bool:
        """Validates the structure and types of the pipe body dictionary.

        Args:
            body: Dictionary containing user message content, stream, and optional search data

        Returns:
            bool: True if body has valid structure and types, False otherwise

        The body must contain:
        - user_message_content as string
        - stream as boolean
        - Optional inlet_error as string
        - Optional search_results as list
        - Optional search_params as dict
        - Optional messages list
        """
        if not isinstance(body, dict):
            return False

        messages = body.get("messages", [])
        if not messages or len(messages) < 2:
            return False

        if (messages[-1].get("role") != "user" or
                messages[-2].get("role") != "assistant"):
            return False

        # Validate mandatory user_message_content field
        if not isinstance(body.get("user_message_content"), str):
            return False

        # Validate optional fields if present
        optional_fields = {
            "inlet_error": str,
            "search_results": list,
            "search_params": dict
        }

        for field, expected_type in optional_fields.items():
            if field in body and not isinstance(body[field], expected_type):
                print(f"Field {field} is not of type {expected_type}")
                return False
        return True

    def pipe(self, body: dict) -> Union[str, Generator, Iterator]:
        """Main pipeline processing method"""
        print(f"pipe:{__name__}")
        if body["inlet_error"]:
            return body["inlet_error"]

        if self.valves.GET_RESPONSE:
            self._initialize_client()
        try:
            stream = body["stream"]
            user_message_string = body["user_message_content"]
            search_results_list = body["search_results"]
            search_params_dict = body["search_params"]
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
