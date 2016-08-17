# encoding: utf-8
import views
from websocket_server.uwsgi_ws_server import uWSGIWebsocketServer

def url_dispatch(path_info):
    
    uname = path_info.replace(".", "_")
    
    if not path_info:
        uname = "home"
    
    func = getattr(views, uname, None)
    if not func:
        return None
    
    return func

def application(env, rs):
    
    if env.get("HTTP_UPGRADE")=="websocket" or env.get("wsgi.url_scheme")=="ws":
        ws_server = uWSGIWebsocketServer()
        return ws_server(env, rs)
    
    path_info = env["PATH_INFO"]
    if path_info.startswith("/"):
        path_info = path_info[1:]
    
    func = url_dispatch(path_info)
    if not func:
        rs("404 Not Found", [("Content-Type", "text/html")])
        return ""
        
    return func(env, rs)
