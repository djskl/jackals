# encoding: utf-8
import uwsgi
import re
import uuid
from jinja2 import Environment, FileSystemLoader

def home(env, rs):
    rs("200 OK", [("Content-Type", "text/html")])
    tmpl_env = Environment(loader = FileSystemLoader("./"))
    template = tmpl_env.get_template("index.html")
    html = template.render(server_name=env["HTTP_HOST"])
    html = html if isinstance(html, str) else html.encode("utf-8")
    return str(html)
    
def foobar(env, rs):
    uwsgi.websocket_handshake(env['HTTP_SEC_WEBSOCKET_KEY'], env.get('HTTP_ORIGIN', ''))
    while True:
        msg = uwsgi.websocket_recv()
        uwsgi.websocket_send(msg)
        
def task_new(env, rs):
    pass

def application(env, rs):
    
    url = env["PATH_INFO"]
    
    if re.match(r"^/$", url):
        return home(env, rs)
    
    if re.match(r"^/foobar", url):
        foobar(env, rs)
    
    

