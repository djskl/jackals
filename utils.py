#encoding: utf-8

_cgi = __import__("cgi")    #防止被from utils import *引入
_threading = __import__("threading")
_urlparse = __import__("urlparse")

__all__ = ["synchronized", "parse_wsgi_post", "parse_wsgi_get"]


def synchronized(func):
    
    _lock = _threading.Lock()
    
    def _wraper(*args, **kargs):
        try:
            _lock.acquire()
            return func(*args, **kargs)
        finally:
            _lock.release()
            
    return _wraper

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
    
    
    
    


