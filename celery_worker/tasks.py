from __future__ import absolute_import

import subprocess
import redis
import json
from celery.utils.log import get_task_logger
from jackals.celery_worker.worker import app
from jackals.settings import WEBSOCKET_REDIS_CHANNEL_URL, CELERY_BACKEND_URL


logger = get_task_logger(__name__)

from time import sleep
from random import randint
@app.task(name="ces")
def ces():
    while True:
        seconds = randint(3, 5)
        sleep(seconds)
        print seconds
        

@app.task(bind=True, name="script_worker")
def script_worker(self, script_file, *args, **kwargs):
    
    if script_file.endswith("pyc"):
        script_file = script_file[:-1]
    
    if not script_file.endswith("py"):
        return -1
    
    channel_conn = redis.StrictRedis.from_url(WEBSOCKET_REDIS_CHANNEL_URL)
    backend_conn = redis.StrictRedis.from_url(CELERY_BACKEND_URL)
    
    taskid = self.request.id
     
    _cmd = ["python", "-u", script_file] + [str(arg) for arg in args]
    for k, v in kwargs:
        _cmd.append("-"+k+" "+v)
        
    p = subprocess.Popen(_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    backend_conn.hset("task:%s"%taskid, "subpid", p.pid)
    
    channel_name = taskid + "_logs"
    
    logger.info("channel_name: %s"%channel_name)
    
    logger.info("start...")
    
    for line in iter(p.stdout.readline, ""):
        if line.endswith("\n"):
            line = line[:-1]
            
        channel_conn.publish(channel_name, json.dumps({
            "type": "LOG",
            "message": line
        }))
        
        logger.info(line)
        
    for line in iter(p.stderr.readline, ""):
        if line.endswith("\n"):
            line = line[:-1]
            
        channel_conn.publish(channel_name, json.dumps({
            "type": "LOG",
            "message": line
        }))
        
        logger.info(line)
    
    logger.info("finish!!!")
    
    return p.poll()
