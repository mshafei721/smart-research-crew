import redis
from src.config.settings import get_settings

settings = get_settings()

def get_redis_connection():
    if not settings.redis_enabled:
        return None
    try:
        r = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            socket_connect_timeout=settings.redis_socket_connect_timeout,
            decode_responses=True
        )
        r.ping()
        return r
    except Exception as e:
        print(f"Redis connection error: {e}")
        return None
