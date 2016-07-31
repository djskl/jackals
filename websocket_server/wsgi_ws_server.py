import uwsgi
import redis
import threading

def handle_client_msg(msg):
    if msg:
        print "receive message:", msg
    else:
        print "recevied an empty message"

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
        
        
class WSGIWebsocketServer(object):
    
    def __init__(self):
        self._redis_conn = redis.StrictRedis()
    
    def __call__(self, env, sr):
        
        channel = make_redis_channels(env["PATH_INFO"])
        
        if not channel:
            raise Exception("path_info is invalid")
        
        sub = Subscriber()
        sub.subscribe(channel)
        
        ws = self.upgrade_websocket(env, sr)
        
        while ws and not ws.closed:
            
            ws_fd = ws.get_file_descriptor()
            rd_fd = sub.get_file_descriptor()
            
            ready = self.select([ws_fd, rd_fd], [], [], 4)
            
            if not ready[0]:
                ws.flush()
            else:
                for fd in ready[0]:
                    if fd == ws_fd:
                        msg = ws.receive()
                        handle_client_msg(msg)
                        
                    elif fd == rd_fd:
                        msg = sub.get_message()
                        if msg:
                            ws.send(msg)
        
        return ""
    
        