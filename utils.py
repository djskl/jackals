import threading

def synchronized(func):
    
    _lock = threading.Lock()
    
    def _wraper(*args, **kargs):
        try:
            _lock.acquire()
            return func(*args, **kargs)
        finally:
            _lock.release()
            
    return _wraper

CHANNEL_PREFIX = "WEBSOCKET"
def make_channel(path_info):
    if path_info.startswith("/"):
        path_info = path_info[1:]
        
    if path_info.endswith("/"):
        path_info = path_info[:-1]
    
    if not path_info:
        return None
    
    return "%s_%s"%(CHANNEL_PREFIX, "_".join(path_info.split("_")))