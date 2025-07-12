"""
Cache integration for Smart Research Crew.

This module provides integration between the Redis cache and the research workflow,
including middleware and startup/shutdown handlers.
"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import get_settings
from config.logging import get_logger
from cache.redis_cache import initialize_cache, close_cache, get_cache, CacheConfig

logger = get_logger(__name__)


async def setup_cache() -> bool:
    """Initialize cache based on application settings."""
    settings = get_settings()

    if not settings.redis_enabled:
        logger.info("Redis cache disabled by configuration")
        return False

    config = CacheConfig(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password,
        socket_timeout=settings.redis_socket_timeout,
        socket_connect_timeout=settings.redis_socket_connect_timeout,
        default_ttl=settings.cache_default_ttl,
        research_cache_ttl=settings.cache_research_ttl,
        section_cache_ttl=settings.cache_section_ttl,
    )

    success = await initialize_cache(config)

    if success:
        logger.info("Cache initialization completed successfully")
    else:
        logger.warning("Cache initialization failed - continuing without cache")

    return success


async def teardown_cache():
    """Close cache connections."""
    await close_cache()
    logger.info("Cache connections closed")


@asynccontextmanager
async def cache_lifespan(app: FastAPI):
    """Application lifespan manager for cache."""
    # Startup
    await setup_cache()
    yield
    # Shutdown
    await teardown_cache()


class CacheMiddleware(BaseHTTPMiddleware):
    """Middleware for cache-related request/response handling."""

    def __init__(self, app, add_cache_headers: bool = True):
        super().__init__(app)
        self.add_cache_headers = add_cache_headers

    async def dispatch(self, request: Request, call_next):
        """Process request and add cache-related headers."""
        # Process the request
        response = await call_next(request)

        if self.add_cache_headers:
            # Add cache-related headers
            cache = await get_cache()

            if cache and cache.is_connected:
                response.headers["X-Cache-Status"] = "enabled"
                response.headers["X-Cache-Backend"] = "redis"
            else:
                response.headers["X-Cache-Status"] = "disabled"

            # Add cache control headers for research endpoints
            if request.url.path.startswith("/sse") or request.url.path.startswith("/api/research"):
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"

        return response


def add_cache_routes(app: FastAPI):
    """Add cache management routes to the application."""

    @app.get("/api/cache/status")
    async def get_cache_status():
        """Get cache status and statistics."""
        cache = await get_cache()

        if not cache:
            return {"status": "disabled", "message": "Cache is not configured or disabled"}

        stats = await cache.get_cache_stats()
        return stats

    @app.post("/api/cache/clear")
    async def clear_cache():
        """Clear all cache entries."""
        cache = await get_cache()

        if not cache or not cache.is_connected:
            return {"status": "error", "message": "Cache not available"}

        try:
            # Clear research cache
            research_count = await cache.invalidate_cache_by_pattern(
                f"{cache.config.research_prefix}*"
            )

            # Clear section cache
            section_count = await cache.invalidate_cache_by_pattern(
                f"{cache.config.section_prefix}*"
            )

            # Clear metadata cache
            metadata_count = await cache.invalidate_cache_by_pattern(
                f"{cache.config.metadata_prefix}*"
            )

            total_cleared = research_count + section_count + metadata_count

            return {
                "status": "success",
                "message": f"Cleared {total_cleared} cache entries",
                "details": {
                    "research_entries": research_count,
                    "section_entries": section_count,
                    "metadata_entries": metadata_count,
                },
            }

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return {"status": "error", "message": f"Failed to clear cache: {str(e)}"}

    @app.post("/api/cache/clear/{cache_type}")
    async def clear_cache_by_type(cache_type: str):
        """Clear cache entries by type (research, section, metadata)."""
        cache = await get_cache()

        if not cache or not cache.is_connected:
            return {"status": "error", "message": "Cache not available"}

        # Map cache types to prefixes
        type_mapping = {
            "research": cache.config.research_prefix,
            "section": cache.config.section_prefix,
            "metadata": cache.config.metadata_prefix,
        }

        if cache_type not in type_mapping:
            return {
                "status": "error",
                "message": f"Invalid cache type. Must be one of: {list(type_mapping.keys())}",
            }

        try:
            pattern = f"{type_mapping[cache_type]}*"
            cleared_count = await cache.invalidate_cache_by_pattern(pattern)

            return {
                "status": "success",
                "message": f"Cleared {cleared_count} {cache_type} cache entries",
            }

        except Exception as e:
            logger.error(f"Failed to clear {cache_type} cache: {e}")
            return {"status": "error", "message": f"Failed to clear {cache_type} cache: {str(e)}"}


# Utility functions for cache key generation
def generate_research_cache_key(topic: str, guidelines: str, sections: list) -> str:
    """Generate a consistent cache key for research results."""
    import hashlib

    # Create a deterministic key from inputs
    key_parts = [topic.strip().lower(), guidelines.strip().lower()]
    key_parts.extend(sorted([s.strip().lower() for s in sections]))
    key_string = "|".join(key_parts)

    # Hash if too long
    if len(key_string) > 200:
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
        return f"research:{key_hash}"

    return f"research:{key_string}"


def generate_section_cache_key(topic: str, section: str, guidelines: str) -> str:
    """Generate a consistent cache key for section results."""
    import hashlib

    key_parts = [topic.strip().lower(), section.strip().lower(), guidelines.strip().lower()]
    key_string = "|".join(key_parts)

    if len(key_string) > 200:
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
        return f"section:{key_hash}"

    return f"section:{key_string}"


# Health check function
async def check_cache_health() -> dict:
    """Check cache health and return status."""
    cache = await get_cache()

    if not cache:
        return {"status": "disabled", "healthy": True, "message": "Cache is disabled"}

    try:
        stats = await cache.get_cache_stats()

        return {
            "status": "enabled",
            "healthy": cache.is_connected,
            "connection_status": stats.get("connection_status", "unknown"),
            "hit_rate": stats.get("hit_rate", 0),
            "total_operations": (
                stats.get("operations", {}).get("cache_hits", 0)
                + stats.get("operations", {}).get("cache_misses", 0)
            ),
        }

    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {"status": "enabled", "healthy": False, "error": str(e)}
