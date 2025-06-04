import redis
import os

class RedisHelper:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisHelper, cls).__new__(cls)
            cls._instance.client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                password=os.getenv("REDIS_PASS", ""),
                decode_responses=True
            )
        return cls._instance

    def get(self, key):
        return self.client.get(key)

    def set_value(self, key, value):
        return self.client.set(key, value)
        

    def publish(self, channel, msg):
        return self.client.publish(channel, msg)


redis_helper = RedisHelper()