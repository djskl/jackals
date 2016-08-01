import uwsgi
from sub.rds import Subscriber
from sub.rds import make_redis_channels as make_channel

def handle_client_msg(msg):
    if msg:
        print "receive message:", msg
    else:
        print "recevied an empty message"
        
        
class WSGIWebsocketServer(object):
    
    def __call__(self, env, sr):
        
        channel = make_channel(env["PATH_INFO"])
        
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
    
        