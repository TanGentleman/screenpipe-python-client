"""
title: Screenpipe Pipe
author: TanGentleman
author_url: https://github.com/TanGentleman
funding_url: https://github.com/TanGentleman
version: 0.5
"""

import json
from typing import Union, Generator, Iterator, List
import logging
from openai import OpenAI
from pydantic import BaseModel, Field

from utils.owui_utils.configuration import PipelineConfig
from utils.owui_utils.pipeline_utils import ResponseUtils


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
