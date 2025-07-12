"""
Redis caching layer for Smart Research Crew.

This module provides caching functionality to improve performance
and reduce API calls for research operations.
"""

from .redis_cache import RedisCache, CacheConfig, cache_manager

__all__ = ["RedisCache", "CacheConfig", "cache_manager"]
