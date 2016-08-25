#encoding: utf-8

from jinja2 import Environment, FileSystemLoader
import utils
import uuid
import sys;sys.path.append(r'/usr/local/eclipse/plugins/org.python.pydev_3.8.0.201409251235/pysrc')
import os
from const import TaskStatus
from settings import SCRIPT_ROOT
import json
from celery_server.app import script_worker
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
    
    #taskid = str(uuid.uuid4())
    taskid = "123456"
    
    script_file = os.path.join(SCRIPT_ROOT, "%s.py"%taskid)
    with open(script_file, "w") as writer:
        writer.write(task_script)
        
    #script_worker.delay(script_file)
    script_worker.apply_async(task_id=taskid)
    
    rs("200 OK", [("Content-Type", "application/json")])
    return json.dumps({
        "code": TaskStatus.SUBMITED,
        "info": taskid
    })


def show_task(env, rs):
    tmpl_env = Environment(loader = FileSystemLoader("./templates"))
    template = tmpl_env.get_template("run.html")
    html = template.render(server_name=env["HTTP_HOST"], taskid="123456")
    html = html if isinstance(html, str) else html.encode("utf-8")
    
    rs("200 OK", [("Content-Type", "text/html")])
    return str(html)
    

def favicon_ico(env, rs):
    rs("200 OK", [("Content-Type", "text/html")])
    return ""