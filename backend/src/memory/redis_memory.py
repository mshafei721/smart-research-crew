import json
from typing import List, Dict, Any
from src.database import get_redis_connection
from src.config.logging import LoggerMixin

class RedisMemory(LoggerMixin):
    """
    A Redis-backed memory implementation for agents.
    Stores messages in Redis lists, with each message as a JSON string.
    """

    def __init__(self, session_id: str, ttl: int = 3600):
        self.session_id = f"agent_memory:{session_id}"
        self.ttl = ttl  # Time-to-live in seconds
        self.redis_client = get_redis_connection()
        if not self.redis_client:
            self.log_warning("Redis connection not available, RedisMemory will not be persistent.")

    def add_message(self, message: Dict[str, Any]):
        """
        Adds a message to the memory.
        """
        if self.redis_client:
            try:
                self.redis_client.rpush(self.session_id, json.dumps(message))
                self.redis_client.expire(self.session_id, self.ttl)
            except Exception as e:
                self.log_error(f"Failed to add message to Redis memory: {e}", exc_info=True)

    def get_messages(self) -> List[Dict[str, Any]]:
        """
        Retrieves all messages from the memory.
        """
        if self.redis_client:
            try:
                messages = self.redis_client.lrange(self.session_id, 0, -1)
                return [json.loads(msg) for msg in messages]
            except Exception as e:
                self.log_error(f"Failed to retrieve messages from Redis memory: {e}", exc_info=True)
        return []

    def clear(self):
        """
        Clears all messages from the memory.
        """
        if self.redis_client:
            try:
                self.redis_client.delete(self.session_id)
            except Exception as e:
                self.log_error(f"Failed to clear Redis memory: {e}", exc_info=True)
