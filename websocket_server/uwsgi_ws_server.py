#encoding:utf-8
import uwsgi
import gevent.select
from websocket_server.wsgi_ws_server import WSGIWebsocketServer

class uWsgiWebSocket(object):
    
    def __init__(self):
        self._closed = False
    
    @property
    def closed(self):
        return self._closed
    
    def send(self, msg):
        try:
            uwsgi.websocket_send(msg)
            return True
        except IOError:
            self.close()
            return False
        
    def receive(self):
        '''
        possible to throw exceptions
        '''
        try:
            return uwsgi.websocket_recv_nb()
        except IOError:
            self.close()
            return None
        
    def get_file_descriptor(self):
        if self._closed:
            return -1
        
        return uwsgi.connection_fd()
    
    
    def flush(self):
        try:
            uwsgi.websocket_recv_nb()
        except IOError:
            self.close()
        
    def close(self):
        self._closed = True
        
class uWSGIWebsocketServer(WSGIWebsocketServer):
    
    def upgrade_websocket(self, env, sr):
        
        #if failed, plase ensure that the opensll has been installed(after installing it , re-install uwsgi) 
        uwsgi.websocket_handshake(env['HTTP_SEC_WEBSOCKET_KEY'], env.get('HTTP_ORIGIN', ''))
            
        return uWsgiWebSocket()
        
    def select(self, rlist, wlist, xlist, timeout=None):
        return gevent.select.select(rlist, wlist, xlist, timeout)
    
