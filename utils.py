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

import cgi
def parse_wsgi_post(env):
    
    post_env = env.copy()
    post_env['QUERY_STRING'] = ''
    
    params = cgi.FieldStorage(
        fp=env['wsgi.input'],
        environ=post_env,
        keep_blank_values=True
    )
    
    return params

import urlparse
def parse_wsgi_get(env):
    qs = env['QUERY_STRING']
    params = urlparse.parse_qs(qs)
    
    for k in params:
        params[k] = params[k][0]
        
    return params
    
    
    
    


