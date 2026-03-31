import redis.asyncio as redis

from configs.redis import RedisConfig

_config = RedisConfig()
redis_client = redis.Redis(
    host=_config.HOST,
    port=_config.PORT,
    db=0,
    decode_responses=True,
)
