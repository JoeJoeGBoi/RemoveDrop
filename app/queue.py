from redis import Redis
from rq import Queue
from .config import REDIS_URL, QUEUE_NAME

_redis = Redis.from_url(REDIS_URL)
queue = Queue(name=QUEUE_NAME, connection=_redis)
