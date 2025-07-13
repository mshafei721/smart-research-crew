"""
Redis caching implementation for Smart Research Crew.

This module provides a Redis-based caching layer to store and retrieve
research results, reducing API calls and improving response times.
"""

import json
import hashlib
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from contextlib import asynccontextmanager
import asyncio

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import ConnectionError, TimeoutError

from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CacheConfig:
    """Configuration for Redis cache."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    decode_responses: bool = True
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    connection_pool_kwargs: Optional[Dict] = None

    # Cache-specific settings
    default_ttl: int = 3600  # 1 hour default TTL
    research_cache_ttl: int = 7200  # 2 hours for research results
    section_cache_ttl: int = 1800  # 30 minutes for individual sections
    max_retries: int = 3
    retry_delay: float = 1.0

    # Key prefixes
    research_prefix: str = "research:"
    section_prefix: str = "section:"
    metadata_prefix: str = "meta:"


class RedisCache:
    """Redis-based cache manager for research data."""

    def __init__(self, config: CacheConfig):
        self.config = config
        self._redis: Optional[Redis] = None
        self._connection_pool = None
        self._is_connected = False
        self._health_check_task = None
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0, "errors": 0}

    async def initialize(self) -> bool:
        """Initialize Redis connection and connection pool."""
        try:
            # Create connection pool
            pool_kwargs = self.config.connection_pool_kwargs or {}
            self._connection_pool = redis.ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                decode_responses=self.config.decode_responses,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                **pool_kwargs,
            )

            # Create Redis client
            self._redis = Redis(connection_pool=self._connection_pool)

            # Test connection
            await self._redis.ping()
            self._is_connected = True

            # Start health check task
            self._health_check_task = asyncio.create_task(self._health_check_loop())

            logger.info(
                f"Redis cache initialized successfully: {self.config.host}:{self.config.port}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            self._is_connected = False
            return False

    async def close(self):
        """Close Redis connection and cleanup resources."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        if self._redis:
            await self._redis.aclose()
            self._redis = None

        if self._connection_pool:
            await self._connection_pool.disconnect()
            self._connection_pool = None

        self._is_connected = False
        logger.info("Redis cache connection closed")

    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._is_connected

    async def _health_check_loop(self):
        """Periodic health check for Redis connection."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                if self._redis:
                    await self._redis.ping()
                    if not self._is_connected:
                        self._is_connected = True
                        logger.info("Redis connection restored")
            except Exception as e:
                if self._is_connected:
                    self._is_connected = False
                    logger.error(f"Redis health check failed: {e}")

    def _generate_cache_key(self, prefix: str, identifier: str, *args) -> str:
        """Generate a unique cache key."""
        # Create a consistent hash from all arguments
        key_parts = [identifier] + [str(arg) for arg in args]
        key_string = ":".join(key_parts)

        # Hash long keys to ensure they don't exceed Redis key length limits
        if len(key_string) > 200:
            key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
            key_string = f"{identifier}:{key_hash}"

        return f"{prefix}{key_string}"

    async def _execute_with_retry(self, operation, *args, **kwargs):
        """Execute Redis operation with retry logic."""
        last_exception = None

        for attempt in range(self.config.max_retries):
            try:
                if not self._is_connected:
                    raise ConnectionError("Redis not connected")

                return await operation(*args, **kwargs)

            except (ConnectionError, TimeoutError) as e:
                last_exception = e
                self._stats["errors"] += 1

                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2**attempt)  # Exponential backoff
                    logger.warning(
                        f"Redis operation failed (attempt {attempt + 1}), retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Redis operation failed after {self.config.max_retries} attempts: {e}"
                    )

            except Exception as e:
                logger.error(f"Unexpected Redis error: {e}")
                self._stats["errors"] += 1
                raise

        raise last_exception

    async def cache_research_result(
        self,
        topic: str,
        guidelines: str,
        sections: List[str],
        result: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache a complete research result."""
        try:
            cache_key = self._generate_cache_key(
                self.config.research_prefix,
                "full_research",
                topic,
                guidelines,
                ":".join(sorted(sections)),
            )

            cache_data = {
                "topic": topic,
                "guidelines": guidelines,
                "sections": sections,
                "result": result,
                "cached_at": time.time(),
                "cache_version": "1.0",
            }

            ttl = ttl or self.config.research_cache_ttl

            await self._execute_with_retry(
                self._redis.setex, cache_key, ttl, json.dumps(cache_data, ensure_ascii=False)
            )

            # Cache metadata separately for search
            metadata_key = self._generate_cache_key(
                self.config.metadata_prefix, "research_meta", cache_key
            )

            metadata = {
                "topic": topic,
                "sections_count": len(sections),
                "cached_at": time.time(),
                "ttl": ttl,
            }

            await self._execute_with_retry(
                self._redis.setex, metadata_key, ttl, json.dumps(metadata)
            )

            self._stats["sets"] += 1
            logger.debug(f"Cached research result: {cache_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to cache research result: {e}")
            return False

    async def get_cached_research_result(
        self, topic: str, guidelines: str, sections: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a cached research result."""
        try:
            cache_key = self._generate_cache_key(
                self.config.research_prefix,
                "full_research",
                topic,
                guidelines,
                ":".join(sorted(sections)),
            )

            cached_data = await self._execute_with_retry(self._redis.get, cache_key)

            if cached_data:
                self._stats["hits"] += 1
                data = json.loads(cached_data)

                # Validate cache version and data integrity
                if data.get("cache_version") == "1.0" and "result" in data:
                    logger.debug(f"Cache hit for research: {cache_key}")
                    return data["result"]
                else:
                    # Invalid cache data, delete it
                    await self._execute_with_retry(self._redis.delete, cache_key)
                    logger.warning(f"Invalid cache data found, deleted: {cache_key}")

            self._stats["misses"] += 1
            logger.debug(f"Cache miss for research: {cache_key}")
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve cached research result: {e}")
            self._stats["misses"] += 1
            return None

    async def cache_section_result(
        self,
        topic: str,
        section: str,
        guidelines: str,
        result: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache an individual section result."""
        try:
            cache_key = self._generate_cache_key(
                self.config.section_prefix, "section_result", topic, section, guidelines
            )

            cache_data = {
                "topic": topic,
                "section": section,
                "guidelines": guidelines,
                "result": result,
                "cached_at": time.time(),
                "cache_version": "1.0",
            }

            ttl = ttl or self.config.section_cache_ttl

            await self._execute_with_retry(
                self._redis.setex, cache_key, ttl, json.dumps(cache_data, ensure_ascii=False)
            )

            self._stats["sets"] += 1
            logger.debug(f"Cached section result: {cache_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to cache section result: {e}")
            return False

    async def get_cached_section_result(
        self, topic: str, section: str, guidelines: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a cached section result."""
        try:
            cache_key = self._generate_cache_key(
                self.config.section_prefix, "section_result", topic, section, guidelines
            )

            cached_data = await self._execute_with_retry(self._redis.get, cache_key)

            if cached_data:
                self._stats["hits"] += 1
                data = json.loads(cached_data)

                if data.get("cache_version") == "1.0" and "result" in data:
                    logger.debug(f"Cache hit for section: {cache_key}")
                    return data["result"]
                else:
                    await self._execute_with_retry(self._redis.delete, cache_key)
                    logger.warning(f"Invalid section cache data found, deleted: {cache_key}")

            self._stats["misses"] += 1
            logger.debug(f"Cache miss for section: {cache_key}")
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve cached section result: {e}")
            self._stats["misses"] += 1
            return None

    async def invalidate_cache_by_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching a pattern."""
        try:
            # Use SCAN to find matching keys (more efficient than KEYS)
            deleted_count = 0
            async for key in self._redis.scan_iter(match=pattern):
                await self._execute_with_retry(self._redis.delete, key)
                deleted_count += 1
                self._stats["deletes"] += 1

            logger.info(f"Invalidated {deleted_count} cache entries matching pattern: {pattern}")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to invalidate cache by pattern {pattern}: {e}")
            return 0

    async def clear_expired_cache(self) -> int:
        """Clear expired cache entries (Redis handles this automatically, but useful for stats)."""
        try:
            # Get cache statistics
            info = await self._execute_with_retry(self._redis.info, "keyspace")

            # Extract expired keys count if available
            expired_count = 0
            for db_info in info.values():
                if isinstance(db_info, dict) and "expires" in db_info:
                    expired_count += db_info.get("expires", 0)

            return expired_count

        except Exception as e:
            logger.error(f"Failed to get expired cache info: {e}")
            return 0

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics and health information."""
        try:
            redis_info = await self._execute_with_retry(self._redis.info)

            return {
                "connection_status": "connected" if self._is_connected else "disconnected",
                "redis_version": redis_info.get("redis_version", "unknown"),
                "used_memory": redis_info.get("used_memory_human", "unknown"),
                "connected_clients": redis_info.get("connected_clients", 0),
                "operations": {
                    "cache_hits": self._stats["hits"],
                    "cache_misses": self._stats["misses"],
                    "cache_sets": self._stats["sets"],
                    "cache_deletes": self._stats["deletes"],
                    "cache_errors": self._stats["errors"],
                },
                "hit_rate": (
                    self._stats["hits"] / (self._stats["hits"] + self._stats["misses"])
                    if (self._stats["hits"] + self._stats["misses"]) > 0
                    else 0
                ),
                "config": {
                    "host": self.config.host,
                    "port": self.config.port,
                    "db": self.config.db,
                    "default_ttl": self.config.default_ttl,
                    "research_cache_ttl": self.config.research_cache_ttl,
                    "section_cache_ttl": self.config.section_cache_ttl,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {
                "connection_status": "error",
                "error": str(e),
                "operations": self._stats.copy(),
            }

    @asynccontextmanager
    async def pipeline(self):
        """Context manager for Redis pipeline operations."""
        if not self._is_connected:
            raise ConnectionError("Redis not connected")

        pipe = self._redis.pipeline()
        try:
            yield pipe
            await pipe.execute()
        except Exception as e:
            logger.error(f"Pipeline operation failed: {e}")
            raise
        finally:
            await pipe.reset()


# Global cache manager instance
cache_manager: Optional[RedisCache] = None


async def initialize_cache(config: CacheConfig) -> bool:
    """Initialize the global cache manager."""
    global cache_manager

    cache_manager = RedisCache(config)
    success = await cache_manager.initialize()

    if success:
        logger.info("Cache manager initialized successfully")
    else:
        logger.error("Failed to initialize cache manager")
        cache_manager = None

    return success


async def get_cache() -> Optional[RedisCache]:
    """Get the global cache manager instance."""
    return cache_manager


async def close_cache():
    """Close the global cache manager."""
    global cache_manager

    if cache_manager:
        await cache_manager.close()
        cache_manager = None
        logger.info("Cache manager closed")


# Cache decorators for easy integration
def cached_research_result(ttl: Optional[int] = None):
    """Decorator for caching research results."""

    def decorator(func):
        async def wrapper(topic: str, guidelines: str, sections: List[str], *args, **kwargs):
            cache = await get_cache()

            if cache and cache.is_connected:
                # Try to get from cache first
                cached_result = await cache.get_cached_research_result(topic, guidelines, sections)
                if cached_result:
                    return cached_result

            # Execute the original function
            result = await func(topic, guidelines, sections, *args, **kwargs)

            # Cache the result
            if cache and cache.is_connected and result:
                await cache.cache_research_result(topic, guidelines, sections, result, ttl)

            return result

        return wrapper

    return decorator


def cached_section_result(ttl: Optional[int] = None):
    """Decorator for caching section results."""

    def decorator(func):
        async def wrapper(topic: str, section: str, guidelines: str, *args, **kwargs):
            cache = await get_cache()

            if cache and cache.is_connected:
                # Try to get from cache first
                cached_result = await cache.get_cached_section_result(topic, section, guidelines)
                if cached_result:
                    return cached_result

            # Execute the original function
            result = await func(topic, section, guidelines, *args, **kwargs)

            # Cache the result
            if cache and cache.is_connected and result:
                await cache.cache_section_result(topic, section, guidelines, result, ttl)

            return result

        return wrapper

    return decorator
