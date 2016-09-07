from celery import Celery, platforms
from celery.utils.log import get_task_logger
import json
from jackals.const import TaskStatus
from celery.signals import after_task_publish
from celery._state import current_app

app = Celery('ctasks')

app.conf.update(
    BROKER_URL = 'amqp://guest@localhost//',
    CELERY_RESULT_BACKEND = 'redis://localhost:6379',
    CELERY_TASK_SERIALIZER = 'json',
    CELERY_RESULT_SERIALIZER = 'json',
    CELERY_ACCEPT_CONTENT=['json']         
)

platforms.C_FORCE_ROOT = True

logger = get_task_logger(__name__)

import subprocess
import redis

@app.task(name="celery_server.app.handle_error")
def handle_error(returncode, taskid):
    conn = redis.StrictRedis()
    channel_name = taskid + "_logs"
    conn.publish(channel_name, json.dumps({
        "type": "STATUS",
        "message": TaskStatus.FAILED
    }))

@app.task(name="celery_server.app.handle_finish")
def handle_finish(returncode, taskid):
    conn = redis.StrictRedis()
    channel_name = taskid + "_logs"
    
    if returncode == 0:
        conn.publish(channel_name, json.dumps({
            "type": "STATUS",
            "message": TaskStatus.SUCCESS
        }))
    else:
        conn.publish(channel_name, json.dumps({
            "type": "STATUS",
            "message": TaskStatus.FAILED
        }))

@app.task(bind=True, name="celery_server.app.script_worker")
def script_worker(self, script_file, *args, **kwargs):
    
    if script_file.endswith("pyc"):
        script_file = script_file[:-1]
    
    if not script_file.endswith("py"):
        return -1
    
    taskid = self.request.id
     
    _cmd = ["python", "-u", script_file] + [str(arg) for arg in args]
    for k, v in kwargs:
        _cmd.append("-"+k+" "+v)
        
    p = subprocess.Popen(_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
    conn = redis.StrictRedis()
    
    channel_name = taskid + "_logs"
    
    logger.info("channel_name: %s"%channel_name)
    
    logger.info("start...")
    
    for line in iter(p.stdout.readline, ""):
        if line.endswith("\n"):
            line = line[:-1]
            
        conn.publish(channel_name, json.dumps({
            "type": "LOG",
            "message": line
        }))
    
        conn.publish(channel_name, json.dumps({
            "type": "STATUS",
            "message": TaskStatus.RUNING,
            "pid": p.pid
        }))
        
        logger.info(line)
        
    for line in iter(p.stderr.readline, ""):
        if line.endswith("\n"):
            line = line[:-1]
            
        conn.publish(channel_name, json.dumps({
            "type": "LOG",
            "message": line
        }))
        
        logger.info(line)
    
    logger.info("finish!!!")
    
    return p.poll()

@after_task_publish.connect
def update_sent_state(sender=None, body=None, **kwargs):
    # the task may not exist if sent using `send_task` which
    # sends tasks by name, so fall back to the default result backend
    # if that is the case.
    task = current_app.tasks.get(sender)
    backend = task.backend if task else current_app.backend

    backend.store_result(body['id'], None, "SENT")



    