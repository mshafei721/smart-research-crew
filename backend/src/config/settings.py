"""
Smart Research Crew - Configuration Management

Centralized settings management with environment variable support
and production-ready defaults.
"""

import os
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Core Application Settings
    app_name: str = "Smart Research Crew API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # CORS Configuration
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]

    # AI/LLM Configuration
    llm_model: str = "openai"
    llm_max_tokens: int = 128000
    openai_api_key: Optional[str] = None

    # Research Configuration
    max_sections: int = 10
    section_timeout: int = 30
    search_timeout: int = 30
    min_topic_length: int = 3
    max_topic_length: int = 200
    max_guidelines_length: int = 1000

    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_request_logging: bool = True

    # Performance Configuration
    max_concurrent_requests: int = 10
    request_timeout: int = 300  # 5 minutes

    # Security Configuration
    enable_rate_limiting: bool = False
    rate_limit_per_minute: int = 30

    # Redis Cache Configuration
    redis_enabled: bool = False
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_socket_timeout: float = 5.0
    redis_socket_connect_timeout: float = 5.0

    # Cache TTL settings (in seconds)
    cache_default_ttl: int = 3600  # 1 hour
    cache_research_ttl: int = 7200  # 2 hours
    cache_section_ttl: int = 1800  # 30 minutes

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_api_key(cls, v):
        """Validate OpenAI API key is provided."""
        if not v:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string if needed."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level is supported."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    @field_validator("max_sections")
    @classmethod
    def validate_max_sections(cls, v):
        """Ensure reasonable section limits."""
        if v < 1 or v > 20:
            raise ValueError("max_sections must be between 1 and 20")
        return v

    @field_validator("redis_port")
    @classmethod
    def validate_redis_port(cls, v):
        """Validate Redis port."""
        if not 1 <= v <= 65535:
            raise ValueError("Redis port must be between 1 and 65535")
        return v

    @field_validator("redis_db")
    @classmethod
    def validate_redis_db(cls, v):
        """Validate Redis database number."""
        if not 0 <= v <= 15:
            raise ValueError("Redis database must be between 0 and 15")
        return v

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings


def validate_environment():
    """Validate required environment variables are present."""
    try:
        settings = get_settings()
        return True
    except Exception as e:
        print(f"Environment validation failed: {e}")
        return False


def create_env_example():
    """Create .env.example file with all available settings."""
    env_example = """# Smart Research Crew - Environment Configuration

# Core Application
APP_NAME=Smart Research Crew API
APP_VERSION=1.0.0
DEBUG=false

# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=true

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
CORS_METHODS=*
CORS_HEADERS=*

# AI/LLM Configuration (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=openai
LLM_MAX_TOKENS=128000

# Research Configuration
MAX_SECTIONS=10
SECTION_TIMEOUT=30
SEARCH_TIMEOUT=30
MIN_TOPIC_LENGTH=3
MAX_TOPIC_LENGTH=200
MAX_GUIDELINES_LENGTH=1000

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
ENABLE_REQUEST_LOGGING=true

# Performance Configuration
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=300

# Security Configuration
ENABLE_RATE_LIMITING=false
RATE_LIMIT_PER_MINUTE=30

# Redis Cache Configuration (Optional)
REDIS_ENABLED=false
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_SOCKET_TIMEOUT=5.0
REDIS_SOCKET_CONNECT_TIMEOUT=5.0

# Cache TTL Settings (in seconds)
CACHE_DEFAULT_TTL=3600
CACHE_RESEARCH_TTL=7200
CACHE_SECTION_TTL=1800
"""
    return env_example


if __name__ == "__main__":
    # Create .env.example file when run directly
    env_example_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env.example"
    )

    with open(env_example_path, "w") as f:
        f.write(create_env_example())

    print(f"Created .env.example at: {env_example_path}")

    # Validate current environment
    if validate_environment():
        print("✅ Environment validation passed")
    else:
        print("❌ Environment validation failed")
