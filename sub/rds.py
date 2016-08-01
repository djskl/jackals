import threading
import redis

def make_redis_channels(path_info):
    
    if path_info.startswith("/"):
        path_info = path_info[1:]
        
    if path_info.endswith("/"):
        path_info = path_info[:-1]
    
    if not path_info:
        return None
    
    return "_".join(path_info.split("/"))


class Subscriber(object):
    
    _lock = threading.RLock()
    
    def __new__(cls, *args, **kwargs):
        if hasattr(cls, "inst"):
            return cls.inst
        
        with cls._lock:
            if not hasattr(cls, "inst"):
                cls.inst = super(Subscriber, cls).__new__(cls, *args, **kwargs)
                
        return cls.inst
    
    def __init__(self):
        self._redis_conn = redis.StrictRedis()
        self._pubsub = self._redis_conn.pubsub()
        
    def subscribe(self, channel):
        self._pubsub.subscribe(channel)
    
    def get_message(self):
        rst = self._pubsub.get_message(True)
        if rst:
            return rst.get("data", None)
        return None
    
    def get_file_descriptor(self):
        return self._pubsub.connection._sock.fileno()