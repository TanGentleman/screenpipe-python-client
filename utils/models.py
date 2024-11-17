"""
Models module for managing LLM configurations and registry.

This module provides a centralized way to define, load, and manage LLM model configurations.
It supports importing/exporting configurations via YAML and provides a registry pattern
for model access.
"""
import logging
from pathlib import Path
from typing import Dict, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

IS_DOCKER = False
HOST = "host.docker.internal" if IS_DOCKER else "localhost"
PORT = 4000
LITELLM_BASE_URL = f"http://{HOST}:{PORT}/v1"

# Configure logging
logger = logging.getLogger(__name__)

class ModelCapabilities(TypedDict, total=False):
    """Capabilities of a model"""
    function_calling: bool
    vision: bool
    local: bool

class ModelConfig(TypedDict, total=False):
    """Configuration of a model"""
    temperature: float
    max_tokens: int


class Model(BaseModel):
    """A model class representing an LLM model configuration."""
    
    base_url: str = Field(..., description="Base API URL for the model service")
    model: str = Field(..., description="Full model name/path e.g. 'meta-llama/Llama-3-70b-chat-hf'")
    concise_name: Optional[str] = Field(None, description="Short display name e.g. 'Llama 3 70B'")
    capabilities: Dict = Field(default_factory=dict, description="Model capabilities like function calling, vision etc")
    config: Dict = Field(default_factory=dict, description="Additional configuration parameters")

    def __str__(self) -> str:
        """Return string representation of the model."""
        return f"{self.concise_name} ({self.model})"

    def __repr__(self) -> str:
        """Return detailed string representation of the model."""
        return f"Model(name='{self.concise_name}', model='{self.model}')"


class ModelRegistry:
    """Singleton registry for managing model configurations."""
    
    _instance = None
    _models: Dict[str, Model] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_model(cls, model_id: str) -> Optional[Model]:
        """Get a model by its ID, lazily loading if needed."""
        registry = cls()
        if not registry._models:
            registry._load_predefined_models()
        return registry._models.get(model_id)

    @classmethod
    def list_models(cls) -> Dict[str, Model]:
        """Get all available models as a dictionary."""
        registry = cls()
        if not registry._models:
            registry._load_predefined_models()
        return registry._models.copy()

    def _load_predefined_models(self) -> None:
        """Load predefined models into registry."""
        models = [
            Model(
                base_url=LITELLM_BASE_URL,
                model="claude-3.5-sonnet",
                concise_name="Claude 3.5 Sonnet", 
                capabilities={"function_calling": True, "vision": True}
            ),
            Model(
                base_url=LITELLM_BASE_URL,
                model="together/Qwen/Qwen2.5-Coder-32B-Instruct",
                concise_name="Qwen 2.5 Coder",
            ),
            Model(
                base_url=LITELLM_BASE_URL,
                model="Llama-3.1-70B",
                concise_name="Llama 3.1 70B",
            ),
            Model(
                base_url=LITELLM_BASE_URL,
                model="openai/gpt-4o-mini",
                concise_name="GPT-4o Mini",
                capabilities={"function_calling": True, "vision": True}
            ),
            Model(
                base_url=LITELLM_BASE_URL,
                model="sambanova/Llama-3.2-90B-Vision-Instruct",
                concise_name="SambaNova Llama 90B Vision",
                capabilities={"vision": True}
            ),
            Model(
                base_url=LITELLM_BASE_URL,
                model="openrouter/google/gemini-exp-1114",
                concise_name="Gemini 1.5 Pro",
            ),
            Model(
                base_url=LITELLM_BASE_URL,
                model="lmstudio/qwen2.5-coder-7b-instruct-mlx",
                concise_name="Qwen 2.5 Coder 7B",
                capabilities={"function_calling": True, "local": True}
            ),
        ]
        
        for model in models:
            self._models[model.model] = model

    @classmethod
    def get_vision_models(cls) -> Dict[str, Model]:
        """Get all models that support vision capabilities."""
        return {
            model_id: model 
            for model_id, model in cls.list_models().items() 
            if model.capabilities.get('vision', False)
        }

    @classmethod
    def get_function_calling_models(cls) -> Dict[str, Model]:
        """Get all models that support function calling."""
        return {
            model_id: model 
            for model_id, model in cls.list_models().items() 
            if model.capabilities.get('function_calling', False)
        }

    @classmethod
    def get_local_models(cls) -> Dict[str, Model]:
        """Get all models that can run locally."""
        return {
            model_id: model
            for model_id, model in cls.list_models().items()
            if (
                model.capabilities is not None
                and model.capabilities.get('local', False)
            )
        }

    @classmethod
    def get_model_names(cls, models_dict: Dict[str, Model] = None) -> list[str]:
        """Get a list of concise names for the specified models dictionary.
        If no dictionary is provided, returns names for all models."""
        if models_dict is None:
            models_dict = cls.list_models()
        return [model.concise_name for model in models_dict.values()]


def export_models_to_yaml(yaml_path: str | Path) -> None:
    """Export all models to a YAML file."""
    try:
        import yaml
    except ImportError:
        logger.error("PyYAML is required for YAML operations. Please install with 'pip install PyYAML'")
        raise

    yaml_path = Path(yaml_path)
    models = ModelRegistry.list_models()
    yaml_models = {}
    
    for model in models.values():
        model_config = {
            "model": model.model,
            "base_url": model.base_url
        }
        
        if model.capabilities:
            model_config["capabilities"] = model.capabilities
            
        if model.config:
            model_config["config"] = model.config
            
        yaml_models[model.concise_name] = model_config
    
    try:    
        with yaml_path.open("w") as f:
            yaml.dump(yaml_models, f, sort_keys=False, default_flow_style=False)
    except IOError as e:
        logger.error(f"Failed to write YAML file: {e}")
        raise


def import_models_from_yaml(yaml_path: str | Path) -> Dict[str, Model]:
    """Import models from a YAML file and return a dictionary of Model instances."""
    try:
        import yaml
    except ImportError:
        logger.error("PyYAML is required for YAML operations. Please install with 'pip install PyYAML'")
        raise

    yaml_path = Path(yaml_path)
    try:
        with yaml_path.open("r") as f:
            yaml_models = yaml.safe_load(f)
    except IOError as e:
        logger.error(f"Failed to read YAML file: {e}")
        raise
    
    imported_models = {}
    for name, config in yaml_models.items():
        model = Model(
            model=config["model"],
            base_url=config["base_url"],
            concise_name=name,
            capabilities=config.get("capabilities", {}),
            config=config.get("config", {})
        )
        imported_models[model.model] = model
        
    return imported_models

def main_export():
    filepath = Path(__file__).parent / "models.yaml"
    export_models_to_yaml(filepath)

def main_import():
    filepath = Path(__file__).parent / "models.yaml"
    imported_models = import_models_from_yaml(filepath)
    print(imported_models)

if __name__ == "__main__":
    registry = ModelRegistry()
    
    print("\nAll Models:")
    print(registry.get_model_names())
    
    print("\nVision Models:")
    print(registry.get_model_names(registry.get_vision_models()))
    
    print("\nFunction Calling Models:")
    print(registry.get_model_names(registry.get_function_calling_models()))
    
    print("\nLocal Models:")
    print(registry.get_model_names(registry.get_local_models()))

    main_export()
    # main_import()
