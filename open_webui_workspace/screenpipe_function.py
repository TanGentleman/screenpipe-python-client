"""
title: Screenpipe Filter
author: TanGentleman
author_url: https://github.com/TanGentleman
funding_url: https://github.com/TanGentleman
version: 0.4
"""

from typing import Union, Generator, Iterator, List
import logging
from openai import OpenAI
from pydantic import BaseModel, Field
from owui_utils.configuration import PipelineConfig
from owui_utils.constants import ALT_FINAL_RESPONSE_SYSTEM_MESSAGE
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
        )
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
        self._initialize_client()
        stream = body["stream"]
        messages = body["messages"]
        try:
            if body["inlet_error"]:
                return body["inlet_error"]
            
            search_results = body.get("search_results", [])
            assert search_results
            search_results_as_string = str(search_results)

            # if body.get("get_response"):
            if self.get_response:
                messages_with_data = ResponseUtils.get_messages_with_screenpipe_data(
                    messages,
                    search_results_as_string
                )
                return self._generate_final_response(self.client, self.response_model, messages_with_data, stream)
            
            epilogue = ""
            return search_results_as_string + epilogue
        except Exception as e:
            self.safe_log_error("Error in pipe", e)
            return "An error occurred in the pipe."
            