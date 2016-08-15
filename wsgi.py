# encoding: utf-8
import re
import uuid
from jinja2 import Environment, FileSystemLoader
from websocket_server.uwsgi_ws_server import uWSGIWebsocketServer
from celery_server.app import script_worker

import sys;sys.path.append(r'/usr/local/eclipse/plugins/org.python.pydev_5.1.2.201606231256/pysrc')

def home(env, rs, taskid):
    rs("200 OK", [("Content-Type", "text/html")])
    tmpl_env = Environment(loader = FileSystemLoader("./templates"))
    template = tmpl_env.get_template("index.html")
    html = template.render(server_name=env["HTTP_HOST"], taskid=taskid)
    html = html if isinstance(html, str) else html.encode("utf-8")
    return str(html)

def application(env, sr):
        
    url = env["PATH_INFO"]
    
    import pydevd;pydevd.settrace()
    
    if re.match(r"^/$", url):
        
        script_file = "/tmp/ces.py"
        taskid = str(uuid.uuid4())
        script_worker.apply_async([script_file], task_id=taskid)
        
        return home(env, sr, taskid)
    
    if env.get("HTTP_UPGRADE")=="websocket" or env.get("wsgi.url_scheme")=="ws":
        ws_server = uWSGIWebsocketServer()
        return ws_server(env, sr)
    
    

