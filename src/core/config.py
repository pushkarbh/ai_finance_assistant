"""
Configuration management for AI Finance Assistant.
Loads settings from config.yaml and environment variables.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


# Load environment variables from .env file
load_dotenv()


class LLMConfig(BaseModel):
    """LLM configuration settings."""
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 2000


class EmbeddingsConfig(BaseModel):
    """Embeddings configuration settings."""
    model: str = "all-MiniLM-L6-v2"
    dimension: int = 384


class RAGConfig(BaseModel):
    """RAG system configuration settings."""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    similarity_threshold: float = 0.7


class MarketDataConfig(BaseModel):
    """Market data configuration settings."""
    primary_provider: str = "yfinance"
    fallback_provider: str = "alpha_vantage"
    cache_ttl_minutes: int = 30
    default_period: str = "1mo"


class UIConfig(BaseModel):
    """UI configuration settings."""
    page_title: str = "AI Finance Assistant"
    page_icon: str = "chart_with_upwards_trend"
    layout: str = "wide"


class WorkflowConfig(BaseModel):
    """Workflow configuration settings."""
    max_iterations: int = 10
    timeout_seconds: int = 60


class AppConfig(BaseModel):
    """Main application configuration."""
    name: str = "AI Finance Assistant"
    version: str = "1.0.0"
    description: str = "Multi-agent financial education and portfolio analysis system"

    llm: LLMConfig = Field(default_factory=LLMConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    market_data: MarketDataConfig = Field(default_factory=MarketDataConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)

    # Paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    knowledge_base_path: Path = Field(default=None)
    faiss_index_path: Path = Field(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        if self.knowledge_base_path is None:
            self.knowledge_base_path = self.project_root / "src" / "data" / "knowledge_base"
        if self.faiss_index_path is None:
            self.faiss_index_path = self.project_root / "src" / "data" / "faiss_index"


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """
    Load configuration from YAML file and environment variables.

    Args:
        config_path: Path to config.yaml file. If None, uses default location.

    Returns:
        AppConfig object with all settings.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config.yaml"

    config_data: Dict[str, Any] = {}

    # Load from YAML if exists
    if Path(config_path).exists():
        with open(config_path, 'r') as f:
            yaml_config = yaml.safe_load(f)
            if yaml_config:
                # Flatten nested config
                if 'app' in yaml_config:
                    config_data.update(yaml_config['app'])
                if 'llm' in yaml_config:
                    config_data['llm'] = yaml_config['llm']
                if 'embeddings' in yaml_config:
                    config_data['embeddings'] = yaml_config['embeddings']
                if 'rag' in yaml_config:
                    config_data['rag'] = yaml_config['rag']
                if 'market_data' in yaml_config:
                    config_data['market_data'] = yaml_config['market_data']
                if 'ui' in yaml_config:
                    config_data['ui'] = yaml_config['ui']
                if 'workflow' in yaml_config:
                    config_data['workflow'] = yaml_config['workflow']

    # Override with environment variables
    if os.getenv('OPENAI_MODEL'):
        if 'llm' not in config_data:
            config_data['llm'] = {}
        config_data['llm']['model'] = os.getenv('OPENAI_MODEL')

    if os.getenv('EMBEDDING_MODEL'):
        if 'embeddings' not in config_data:
            config_data['embeddings'] = {}
        config_data['embeddings']['model'] = os.getenv('EMBEDDING_MODEL')

    return AppConfig(**config_data)


def get_openai_api_key() -> str:
    """Get OpenAI API key from environment."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Please set it in your .env file or environment."
        )
    return api_key


def get_anthropic_api_key() -> str:
    """Get Anthropic API key from environment."""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not found. Please set it in your .env file or environment."
        )
    return api_key


def get_alpha_vantage_api_key() -> Optional[str]:
    """Get Alpha Vantage API key from environment (optional)."""
    return os.getenv('ALPHA_VANTAGE_API_KEY')


# Global config instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reset_config():
    """Reset the global configuration (useful for testing)."""
    global _config
    _config = None
