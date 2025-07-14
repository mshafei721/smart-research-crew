import pytest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import get_redis_connection
from src.config.settings import Settings

# Provide a dummy API key for test settings
TEST_SETTINGS = {"openai_api_key": "test_key"}

@patch("redis.Redis")
def test_get_redis_connection_enabled(mock_redis):
    """Test that a Redis connection is returned when enabled."""
    settings = Settings(redis_enabled=True, **TEST_SETTINGS)
    mock_redis_instance = MagicMock()
    mock_redis.return_value = mock_redis_instance

    with patch("src.database.settings", settings):
        conn = get_redis_connection()
        assert conn is not None
        mock_redis.assert_called_once_with(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            socket_connect_timeout=settings.redis_socket_connect_timeout,
            decode_responses=True
        )
        mock_redis_instance.ping.assert_called_once()

@patch("redis.Redis")
def test_get_redis_connection_disabled(mock_redis):
    """Test that no Redis connection is returned when disabled."""
    settings = Settings(redis_enabled=False, **TEST_SETTINGS)

    with patch("src.database.settings", settings):
        conn = get_redis_connection()
        assert conn is None
        mock_redis.assert_not_called()

@patch("redis.Redis")
def test_get_redis_connection_error(mock_redis):
    """Test that None is returned on a connection error."""
    settings = Settings(redis_enabled=True, **TEST_SETTINGS)
    mock_redis_instance = MagicMock()
    mock_redis_instance.ping.side_effect = Exception("Connection failed")
    mock_redis.return_value = mock_redis_instance

    with patch("src.database.settings", settings):
        conn = get_redis_connection()
        assert conn is None