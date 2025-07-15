import pytest
from unittest.mock import patch, MagicMock
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.memory.redis_memory import RedisMemory

@patch("src.memory.redis_memory.get_redis_connection")
def test_redis_memory_init(mock_get_redis_connection):
    mock_redis_client = MagicMock()
    mock_get_redis_connection.return_value = mock_redis_client

    memory = RedisMemory("test_session")
    mock_get_redis_connection.assert_called_once()
    assert memory.session_id == "agent_memory:test_session"
    assert memory.ttl == 3600
    assert memory.redis_client == mock_redis_client

@patch("src.memory.redis_memory.get_redis_connection")
def test_redis_memory_add_message(mock_get_redis_connection):
    mock_redis_client = MagicMock()
    mock_get_redis_connection.return_value = mock_redis_client

    memory = RedisMemory("test_session")
    message = {"role": "user", "content": "hello"}
    memory.add_message(message)

    mock_redis_client.rpush.assert_called_once_with(memory.session_id, json.dumps(message))
    mock_redis_client.expire.assert_called_once_with(memory.session_id, memory.ttl)

@patch("src.memory.redis_memory.get_redis_connection")
def test_redis_memory_get_messages(mock_get_redis_connection):
    mock_redis_client = MagicMock()
    mock_get_redis_connection.return_value = mock_redis_client
    mock_redis_client.lrange.return_value = [json.dumps({"role": "user", "content": "hello"}), json.dumps({"role": "assistant", "content": "hi"})]

    memory = RedisMemory("test_session")
    messages = memory.get_messages()

    mock_redis_client.lrange.assert_called_once_with(memory.session_id, 0, -1)
    assert messages == [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]

@patch("src.memory.redis_memory.get_redis_connection")
def test_redis_memory_clear(mock_get_redis_connection):
    mock_redis_client = MagicMock()
    mock_get_redis_connection.return_value = mock_redis_client

    memory = RedisMemory("test_session")
    memory.clear()

    mock_redis_client.delete.assert_called_once_with(memory.session_id)

@patch("src.memory.redis_memory.get_redis_connection", return_value=None)
def test_redis_memory_no_connection(mock_get_redis_connection):
    memory = RedisMemory("test_session")
    assert memory.redis_client is None

    # Ensure methods don't raise errors when no connection
    memory.add_message({"role": "user", "content": "test"})
    assert memory.get_messages() == []
    memory.clear()
