#encoding: utf-8

from jinja2 import Environment, FileSystemLoader
import utils

# import sys;sys.path.append(r'/usr/local/eclipse/plugins/org.python.pydev_5.1.2.201606231256/pysrc')
# import pydevd;pydevd.settrace()

def home(env, rs):
    rs("200 OK", [("Content-Type", "text/html")])
    tmpl_env = Environment(loader = FileSystemLoader("./templates"))
    template = tmpl_env.get_template("index.html")
    html = template.render(server_name=env["HTTP_HOST"])
    html = html if isinstance(html, str) else html.encode("utf-8")
    return str(html)

def submit_task(env, rs):
    params = utils.parse_wsgi_post(env)
    
def favicon_ico(env, rs):
    rs("200 OK", [("Content-Type", "text/html")])
    return ""