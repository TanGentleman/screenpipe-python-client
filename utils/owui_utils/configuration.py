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
DEFAULT_LLM_API_BASE_URL = f"{URL_BASE}:11434/v1"
DEFAULT_LLM_API_KEY = SENSITIVE_KEY or "API-KEY-HERE"
DEFAULT_NATIVE_TOOL_CALLING = False
GET_RESPONSE = False

# NOTE: If NATIVE_TOOL_CALLING is True, tool model is used instead of the json model

# Model Configuration
DEFAULT_TOOL_MODEL = "gpt-4o-mini"
DEFAULT_JSON_MODEL = "qwen2.5:3b"
DEFAULT_RESPONSE_MODEL = "qwen2.5:3b"

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
