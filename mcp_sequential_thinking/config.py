import yaml
from pydantic import BaseModel, Field
from typing import Optional
import os

# Define Pydantic models for type-safe configuration
class StorageConfig(BaseModel):
    type: str = "sqlite"
    path: str = "sequential_thinking.db"

class SemanticAnalysisConfig(BaseModel):
    enabled: bool = True
    default_lang: str = Field("en", alias="defaultLang")

class AutomaticPromptsConfig(BaseModel):
    enabled: bool = True

class FeaturesConfig(BaseModel):
    semantic_analysis: SemanticAnalysisConfig = Field(default_factory=SemanticAnalysisConfig, alias="semanticAnalysis")
    automatic_prompts: AutomaticPromptsConfig = Field(default_factory=AutomaticPromptsConfig, alias="automaticPrompts")

class AppConfig(BaseModel):
    storage: StorageConfig = Field(default_factory=StorageConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)

def load_config() -> AppConfig:
    """
    Loads configuration from config.yaml, providing default values if the file
    or specific settings are missing.
    """
    # Default config
    config_data = {
        'storage': {'type': 'sqlite', 'path': 'sequential_thinking.db'},
        'features': {
            'semanticAnalysis': {'enabled': True, 'defaultLang': 'en'},
            'automaticPrompts': {'enabled': True}
        }
    }

    # Find config.yaml in the project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "config.yaml")

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
                # Deep merge yaml_data into config_data
                if yaml_data:
                    if 'storage' in yaml_data:
                        config_data['storage'].update(yaml_data['storage'])
                    if 'features' in yaml_data:
                        if 'semanticAnalysis' in yaml_data['features']:
                            config_data['features']['semanticAnalysis'].update(yaml_data['features']['semanticAnalysis'])
                        if 'automaticPrompts' in yaml_data['features']:
                            config_data['features']['automaticPrompts'].update(yaml_data['features']['automaticPrompts'])
        except Exception as e:
            print(f"Warning: Could not load or parse config.yaml. Using default settings. Error: {e}")
    
    return AppConfig.model_validate(config_data)

# Load the configuration once when the module is imported
config = load_config()
