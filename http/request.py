import cgi

class HttpRequest(object):
    
    def __init__(self, environ):
        self.path_info = environ["PATH_INFO"]
        self.method = environ['REQUEST_METHOD'].upper()
        self.env = environ.copy()
        
    def _get_post(self):
        if not hasattr(self, '_post'):
            self._post = {x[0]:x[1][0] for x in cgi.parse(self.env["wsgi.input"], self.env).items()}
        return self._post

    def _set_post(self, post):
        self._post = post
        
    POST = property(_get_post, _set_post)