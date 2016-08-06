import uwsgi
from channels import RedisChannel
from utils import make_channel

def handle_client_msg(msg):
    if msg:
        print "receive message:", msg
    else:
        print "recevied an empty message"
     
class WSGIWebsocketServer(object):
    
    def __call__(self, env, sr):
        
        channel_name = make_channel(env["PATH_INFO"])
        
        if not channel_name:
            raise Exception("path_info is invalid")
        
        outer_channel = RedisChannel()
        outer_channel.subscribe(channel_name)
        
        ws_conn = self.upgrade_websocket(env, sr)
        
        while ws_conn and not ws_conn.closed:
            
            ws_fd = ws_conn.get_file_descriptor()
            rd_fd = outer_channel.get_file_descriptor()
            
            ready = self.select([ws_fd, rd_fd], [], [], 4)
            
            if not ready[0]:
                ws_conn.flush()
            else:
                for fd in ready[0]:
                    if fd == ws_fd:
                        msg = ws_conn.receive()
                        handle_client_msg(msg)
                        
                    elif fd == rd_fd:
                        msg = outer_channel.get_message(channel_name)
                        if msg:
                            ws_conn.send(msg)
        
        return ""
    
        