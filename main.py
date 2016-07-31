# encoding: utf-8
import re
from jinja2 import Environment, FileSystemLoader
from websocket_server.uwsgi_ws_server import uWSGIWebsocketServer

def home(env, rs):
    rs("200 OK", [("Content-Type", "text/html")])
    tmpl_env = Environment(loader = FileSystemLoader("./templates"))
    template = tmpl_env.get_template("index.html")
    html = template.render(server_name=env["HTTP_HOST"])
    html = html if isinstance(html, str) else html.encode("utf-8")
    return str(html)

def application(env, sr):
    
    url = env["PATH_INFO"]
    
    if re.match(r"^/$", url):
        return home(env, sr)
    
    if env.get("HTTP_UPGRADE")=="websocket" or env.get("wsgi.url_scheme")=="ws":
        ws_server = uWSGIWebsocketServer()
        return ws_server(env, sr)
    
    

