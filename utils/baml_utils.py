import os
from typing import Optional
from baml_client import b
from baml_client.types import SearchParameters
from baml_py.errors import (
    BamlError,
    BamlValidationError
)
from baml_py import ClientRegistry

from utils.owui_utils.pipeline_utils import check_for_env_key
cr = ClientRegistry()

class BamlConfig:
    def __init__(self, model: str, base_url: str, api_key: str):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        # Other parameters
        # self.temperature = 0.7

BAML_MODELS = ["OllamaQwen", "GeminiFlash"]

def baml_generate_search_params(
        query: str,
        current_iso_timestamp: str,
        config: Optional[BamlConfig] = None) -> SearchParameters | str:
    """
    Constructs search parameters from a user message and timestamp.
    Handles potential BAML errors and provides detailed error information.

    Args:
        user_message: The raw query message from the user
        current_iso_timestamp: Current timestamp in ISO format

    Returns:
        SearchParameters object or error string
    """
    try:
        if config:
            if config.model in BAML_MODELS:
                cr.set_primary(config.model)
            else:
                cr.add_llm_client(name='CustomClient', provider='openai', options={
                    "model": config.model,
                    "base_url": config.base_url,
                    "api_key": check_for_env_key(config.api_key)
                    # TODO: Add hyperparameters
                })
                cr.set_primary('CustomClient')
        response = b.ConstructSearch(query, current_iso_timestamp, { "client_registry": cr })
        return response
    except BamlValidationError as e:
        print(
            f"Validation Error:\nPrompt: {e.prompt}\nOutput: {e.raw_output}\nMessage: {e.message}")
        return e.raw_output
    except BamlError as e:
        print(f"BAML Error: {e}")
        raise


def baml_generate_search_params_stream(
        query: str,
        current_iso_timestamp: str) -> SearchParameters | str:
    """
    Streams the construction of search parameters, showing intermediate results.
    Handles potential BAML errors and provides detailed error information.
    """
    try:
        stream = b.stream.ConstructSearch(
            query, current_iso_timestamp)
        for msg in stream:
            print(f"Partial result: {msg}")
        return stream.get_final_response()
    except BamlValidationError as e:
        print(
            f"Validation Error:\nPrompt: {e.prompt}\nOutput: {e.raw_output}\nMessage: {e.message}")
        return e.raw_output
    except BamlError as e:
        print(f"BAML Error: {e}")
        raise
