"""Configuration management for MCP Memos Server."""

import os
from typing import Optional
from pydantic import BaseModel, Field, AnyHttpUrl
from pydantic_settings import BaseSettings


class MemosConfig(BaseSettings):
    """Configuration for Memos API connection."""
    
    # Required settings
    memos_url: AnyHttpUrl = Field(
        ..., 
        description="Base URL of your Memos server (e.g., https://memos.example.com)"
    )
    # API key is now optional - can be provided by user at runtime
    memos_api_key: Optional[str] = Field(
        default=None, 
        description="API key for Memos authentication (optional - can be provided by user)"
    )
    
    # Optional settings
    default_visibility: str = Field(
        default="PRIVATE", 
        description="Default visibility for new memos (PRIVATE, PROTECTED, PUBLIC)"
    )
    max_search_results: int = Field(
        default=50, 
        description="Maximum number of search results to return"
    )
    timeout: int = Field(
        default=30, 
        description="HTTP request timeout in seconds"
    )
    
    model_config = {
        "env_file": ".env",
        "env_prefix": "",
        "case_sensitive": False
    }


def get_config() -> MemosConfig:
    """Get configuration instance."""
    return MemosConfig()


def validate_config(require_api_key: bool = False) -> bool:
    """Validate that all required configuration is present.
    
    Args:
        require_api_key: Whether to require API key in config (default: False)
    """
    try:
        config = get_config()
        if require_api_key:
            return bool(config.memos_url and config.memos_api_key)
        else:
            return bool(config.memos_url)
    except Exception:
        return False
