from typing import Any, Optional
from functools import lru_cache
from datetime import datetime, timedelta

class Cache:
    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl):
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Any):
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache, key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        self.cache[key] = (value, datetime.now())

# Create a global cache instance
object_cache = Cache()

@lru_cache(maxsize=100)
def expensive_computation(arg1, arg2):
    # This is a placeholder for any expensive computation
    return arg1 + arg2
