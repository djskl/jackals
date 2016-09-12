_cgi = __import__("cgi")
_threading = __import__("threading")
_urlparse = __import__("urlparse")
_contextmanager = __import__("contextlib.contextmanager")

__all__ = ["synchronized", "make_channel", "parse_wsgi_post", "parse_wsgi_get"]

@_contextmanager
def lockcontext(lock):
    lock.acquire()
    try:
        yield
    finally:
        lock.release()

def synchronized(func):
    
    _lock = _threading.Lock()
    
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

def parse_wsgi_post(env):
    
    post_env = env.copy()
    post_env['QUERY_STRING'] = ''
    
    params = _cgi.FieldStorage(
        fp=env['wsgi.input'],
        environ=post_env,
        keep_blank_values=True
    )
    
    return params

def parse_wsgi_get(env):
    qs = env['QUERY_STRING']
    params = _urlparse.parse_qs(qs)
    
    for k in params:
        params[k] = params[k][0]
        
    return params
    
    
    
    


