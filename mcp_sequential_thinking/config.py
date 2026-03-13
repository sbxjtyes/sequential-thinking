import yaml
from pydantic import BaseModel, Field
from typing import Optional
import os

# Define Pydantic models for type-safe configuration


class SemanticAnalysisConfig(BaseModel):
    enabled: bool = True
    default_lang: str = Field("en", alias="defaultLang")

class AutomaticPromptsConfig(BaseModel):
    enabled: bool = True

class ExtendedThinkingConfig(BaseModel):
    """Claude-inspired: multi-angle exploration, self-check, adaptive depth."""
    enabled: bool = True

class FeaturesConfig(BaseModel):
    semantic_analysis: SemanticAnalysisConfig = Field(default_factory=SemanticAnalysisConfig, alias="semanticAnalysis")
    automatic_prompts: AutomaticPromptsConfig = Field(default_factory=AutomaticPromptsConfig, alias="automaticPrompts")
    extended_thinking: ExtendedThinkingConfig = Field(default_factory=ExtendedThinkingConfig, alias="extendedThinking")

class AppConfig(BaseModel):
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)

def load_config() -> AppConfig:
    """
    Loads configuration from config.yaml, providing default values if the file
    or specific settings are missing.
    """
    # Default config
    config_data = {
        'features': {
            'semanticAnalysis': {'enabled': True, 'defaultLang': 'en'},
            'automaticPrompts': {'enabled': True},
            'extendedThinking': {'enabled': True}
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
                    if 'features' in yaml_data:
                        feats = yaml_data['features']
                        for key, target in [
                            ('semanticAnalysis', 'semanticAnalysis'),
                            ('automaticPrompts', 'automaticPrompts'),
                            ('extendedThinking', 'extendedThinking'),
                        ]:
                            if key in feats and isinstance(feats[key], dict):
                                config_data['features'][target].update(feats[key])
        except Exception as e:
            print(f"Warning: Could not load or parse config.yaml. Using default settings. Error: {e}")
    
    return AppConfig.model_validate(config_data)

# Load the configuration once when the module is imported
config = load_config()
