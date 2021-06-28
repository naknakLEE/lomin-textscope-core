from typing import Optional
from aioredis import Redis, create_redis_pool

from app.common.const import get_settings


settings = get_settings()


class RedisCache:
    def __init__(self):
        self.redis_cache: Optional[Redis] = None

    async def init_cache(self):
        self.redis_cache = await create_redis_pool(
            f"redis://{settings.REDIS_IP_ADDR}:{settings.REDIS_IP_PORT}/0?encoding=utf-8"
        )

    async def keys(self, pattern):
        return await self.redis_cache.keys(pattern)

    async def set(self, key, value):
        return await self.redis_cache.set(key, value)

    async def get(self, key):
        return await self.redis_cache.get(key)

    async def close(self):
        self.redis_cache.close()
        await self.redis_cache.wait_closed()


redis_cache = RedisCache()
