#coding:utf-8

'''
返回到上一级目录，执行：celery worker -A celery_worker.worker -l info
'''

from __future__ import absolute_import

import json
import time
import redis
from celery import Celery, platforms
from jackals.const import TaskStatus
from jackals.settings import CELERY_AMQP_URL, CELERY_BACKEND_URL
app = Celery(
    'ctasks',
    include=['celery_worker.tasks']
)

platforms.C_FORCE_ROOT = True   #for root user

app.conf.update(
    BROKER_URL = CELERY_AMQP_URL,
    CELERY_RESULT_BACKEND = CELERY_BACKEND_URL,
    CELERY_TASK_SERIALIZER = 'json',
    CELERY_RESULT_SERIALIZER = 'json',
    CELERY_ACCEPT_CONTENT=['json'],
    CELERY_TRACK_STARTED=True,     
    CELERY_SEND_EVENTS=True
)

def status_monitor(worker):
    '''
    state.event(event)
    task = state.tasks.get(event['uuid'])
    '''
#     state = worker.events.State()
    rconn = redis.StrictRedis.from_url(CELERY_BACKEND_URL)
    
    #task-started: uuid, hostname, timestamp, pid
    def task_started(event):
        taskid = event["uuid"]        
        
        rconn.hmset("task:%s"%taskid, {
            "pid": event["pid"],
            "status": TaskStatus.RUNING,
            "host": event["hostname"],
            "stime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(event["timestamp"]))
        })
        
        channel_name = taskid + "_logs"
        rconn.publish(channel_name, json.dumps({
            "type": "STATUS",
            "message": TaskStatus.RUNING
        }))

        print "%s start to run"%taskid

    #task-succeeded: uuid, result, runtime, hostname, timestamp
    def task_succeeded(event):
        taskid = event["uuid"]    
        
        channel_name = taskid + "_logs"
        rst = event["result"].strip()
        if rst.startswith("'"):
            rst = rst[1:]
        if rst.endswith("'"):
            rst = rst[:-1]
        try:
            rst = int(rst)
        except ValueError:
            rst = -1
            
        if rst == 0:
            rconn.hmset("task:%s"%taskid, {
                "status": TaskStatus.SUCCESS,
                "ftime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(event["timestamp"]))
            })
            rconn.publish(channel_name, json.dumps({
                "type": "STATUS",
                "message": TaskStatus.SUCCESS
            }))
            print "%s succeed"%taskid
        else:
            rconn.hmset("task:%s"%taskid, {
                "status": TaskStatus.FAILED,
                "ftime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(event["timestamp"]))
            })
            rconn.publish(channel_name, json.dumps({
                "type": "STATUS",
                "message": TaskStatus.FAILED
            }))
            print "%s failed!!!"%taskid

    #task-revoked(uuid, terminated, signum, expired)
    def task_revoked(event):
        taskid = event["uuid"]    
        
        rconn.hmset("task:%s"%taskid, {
            "status": TaskStatus.KILLED,
            "ftime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        })
        
        channel_name = taskid + "_logs"
        rconn.publish(channel_name, json.dumps({
            "type": "STATUS",
            "message": TaskStatus.KILLED
        }))
        print "%s killed!!!"%taskid
        
    #task-failed: uuid, exception, traceback, hostname, timestamp
    def task_failed(event):
        taskid = event["uuid"]    
        
        rconn.hmset("task:%s"%taskid, {
            "status": TaskStatus.FAILED,
            "stime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(event["timestamp"]))
        })
        
        channel_name = taskid + "_logs"
        rconn.publish(channel_name, json.dumps({
            "type": "STATUS",
            "message": TaskStatus.FAILED
        }))
        print "%s failed!!!"%taskid
        
    #hostname, timestamp, freq, sw_ident, sw_ver, sw_sys    
    def worker_offline(event):
        print "worker_offline"
    
    #hostname, timestamp, freq, sw_ident, sw_ver, sw_sys
    def worker_online(event):
        print "worker_online"
        
    #hostname, timestamp, freq, sw_ident, sw_ver, sw_sys, active, processed
    def worker_heartbeat(event):
        print event["hostname"]
    
    with worker.connection() as connection:
        recv = worker.events.Receiver(
            connection,
            handlers={
                'task-started': task_started,
                'task-succeeded': task_succeeded,
                'task-revoked': task_revoked,
                'task-failed': task_failed,
                
                'worker-online': worker_online,
                'worker-heartbeat': worker_heartbeat,
                'worker-offline': worker_offline
            }
        )
        print "status monitor starts work ..."
        recv.capture(limit=None, timeout=None, wakeup=True)

if __name__ == "__main__": 
    status_monitor(app)

