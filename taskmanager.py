'''
Created on Sep 7, 2016

@author: root
'''
import time
import redis
from jackals.celery_worker.tasks import script_worker
from jackals.celery_worker.worker import app, REDIS_BACKEND_URL
from jackals.const import TaskStatus

def execute_task(taskid, script_file):
    
    rconn = redis.StrictRedis.from_url(REDIS_BACKEND_URL)
    
    rconn.hmset("task:%s"%taskid, {
        "status": TaskStatus.PENDING,
        "ptime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    })
    
    return script_worker.apply_async([script_file], task_id=taskid)

def kill_task(taskid):
    task_info = query_task(taskid)
    if int(task_info["status"]) == TaskStatus.PENDING:
        rconn = redis.StrictRedis.from_url(REDIS_BACKEND_URL)
        rconn.hmset("task:%s"%taskid, {
            "status": TaskStatus.FAILED,
            "ftime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        })
    app.control.revoke(taskid, terminate=True)
    
def query_task(taskid):        
#     ins = app.control.inspect()
#     info = ins.query_task(taskid)
    rconn = redis.StrictRedis.from_url(REDIS_BACKEND_URL)
    task_key = "task:%s"%taskid
    
    task_info = rconn.hgetall(task_key)
    
    return task_info

def task_exists(taskid):
    rconn = redis.StrictRedis.from_url(REDIS_BACKEND_URL)
    task_key = "task:%s"%taskid
    
    return rconn.exists(task_key)
    
    
    
