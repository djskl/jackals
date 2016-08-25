#encoding: utf-8

from jinja2 import Environment, FileSystemLoader
import utils
import uuid
import sys;sys.path.append(r'/usr/local/eclipse/plugins/org.python.pydev_5.1.2.201606231256/pysrc')
import os
from const import TaskStatus
from settings import SCRIPT_ROOT
import json
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
    
    task_title = params.getvalue("task-title")
    task_script = params.getvalue("task-script-file")
    
    if not task_script or not task_title:
        rs("200 OK", [("Content-Type", "application/json")])
        return json.dumps({
            "code": TaskStatus.CREATE_ERR,
            "info": "incomplete task info!"
        })
    
    taskid = str(uuid.uuid4())
    script_file = os.path.join(SCRIPT_ROOT, "%s.py"%taskid)
    with open(script_file, "w") as writer:
        writer.write(task_script)
        
    return "OK"
    
    
def favicon_ico(env, rs):
    rs("200 OK", [("Content-Type", "text/html")])
    return ""