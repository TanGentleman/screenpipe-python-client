import os
from dataclasses import dataclass
from typing import List, Tuple

# Sensitive data replacements
REPLACEMENT_TUPLES = []

# Configuration defaults
IS_DOCKER = True
DEFAULT_SCREENPIPE_PORT = 3030
URL_BASE = "http://host.docker.internal" if IS_DOCKER else "http://localhost"
DEFAULT_LLM_API_BASE_URL = f"{URL_BASE}:11434/v1"
DEFAULT_LLM_API_KEY = "API-KEY-HERE"

# Model settings
DEFAULT_FILTER_MODEL = "qwen2.5-coder:latest"
DEFAULT_RESPONSE_MODEL = "qwen2.5:3b"
DEFAULT_FORCE_TOOL_CALLING = False
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
    filter_model: str
    force_tool_calling: bool
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
            filter_model=os.getenv('FILTER_MODEL', DEFAULT_FILTER_MODEL),
            force_tool_calling=get_bool_env('FORCE_TOOL_CALLING', DEFAULT_FORCE_TOOL_CALLING),
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


def create_config() -> PipelineConfig:
    """Get the configuration from the environment"""
    from dotenv import load_dotenv
    load_dotenv(override=True)
    return PipelineConfig.from_env()
