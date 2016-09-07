#encoding: utf-8

from jinja2 import Environment, FileSystemLoader
import utils
import uuid
import os
import json
import signal

from jackals.const import TaskStatus

from settings import SCRIPT_ROOT

import sys;sys.path.append(r'/usr/local/eclipse/plugins/org.python.pydev_3.8.0.201409251235/pysrc')
# import pydevd;pydevd.settrace()

def home(env, rs):
    rs("200 OK", [("Content-Type", "text/html")])
    tmpl_env = Environment(loader = FileSystemLoader("./templates"))
    template = tmpl_env.get_template("index.html")
        
    kwargs = {
        "server_name": env["HTTP_HOST"],
        "all_status": TaskStatus.list()
    }
    html = template.render(**kwargs)
    html = html if isinstance(html, str) else html.encode("utf-8")
    return str(html)

def submit_task(env, rs):
    
    params = utils.parse_wsgi_post(env)
        
    task_title = params.getvalue("task-title")
    task_script = params.getvalue("task-script-file")
    
    if not task_script or not task_title:
        rs("200 OK", [("Content-Type", "application/json")])
        return json.dumps({
            "status": TaskStatus.FAILED,
            "info": "incomplete task info!"
        })
    
    taskid = str(uuid.uuid4())
    
    script_file = os.path.join(SCRIPT_ROOT, "%s.py"%taskid)
    with open(script_file, "w") as writer:
        writer.write(task_script)
        
    script_worker.apply_async([script_file], task_id=taskid, link = handle_finish.s(taskid), link_error = handle_error.s(taskid))
    
    rs("200 OK", [("Content-Type", "application/json")])
    return json.dumps({
        "status": TaskStatus.PENDING,
        "info": taskid
    })
    

def stop_task(env, sr):
    params = utils.parse_wsgi_post(env)
    
    taskid = params.getvalue("taskid")
    status = int(params.getvalue("status"))
    
    if status == TaskStatus.PENDING:
        app.control.revoke(str(taskid))
    
    if status == TaskStatus.RUNING:
        os.kill(int(taskid), signal.SIGKILL)
        
    sr("200 OK", [("Content-Type", "text/html")])
    return ""    

def show_task(env, sr):
    
    params = utils.parse_wsgi_get(env)
    
    task_id = params.get("taskid")
    if not task_id:
        sr("404 NOT FOUND", [("Content-Type", "text/html")])
        return ""
    
    async_rst = app.AsyncResult(task_id)
    if async_rst.status != "SENT":
        sr("404 NOT FOUND", [("Content-Type", "text/html")])
        return "%s doesn't exist!"%task_id
    
    tmpl_env = Environment(loader = FileSystemLoader("./templates"))
    template = tmpl_env.get_template("run.html")
    
    kwargs = {
        "server_name": env["HTTP_HOST"],
        "taskid": task_id,
        "title": task_id,
        "all_status": TaskStatus.list()
    }
    html = template.render(**kwargs)
    html = html if isinstance(html, str) else html.encode("utf-8")
    
    sr("200 OK", [("Content-Type", "text/html")])
    return str(html)
    

def favicon_ico(env, rs):
    rs("200 OK", [("Content-Type", "text/html")])
    return ""