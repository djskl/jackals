# encoding: utf-8
import re
from jinja2 import Environment, FileSystemLoader
from websocket_server.uwsgi_ws_server import uWSGIWebsocketServer

def home(env, rs):
    rs("200 OK", [("Content-Type", "text/html")])
    tmpl_env = Environment(loader = FileSystemLoader("./"))
    template = tmpl_env.get_template("index.html")
    html = template.render(server_name=env["HTTP_HOST"])
    html = html if isinstance(html, str) else html.encode("utf-8")
    return str(html)

def application(env, sr):
    
    url = env["PATH_INFO"]
    
    ws_server = uWSGIWebsocketServer()
    
    if re.match(r"^/$", url):
        return home(env, sr)
    
    if url.startswith("ws"):
        ws_server(env, sr)
    
    

