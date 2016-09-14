#coding:utf-8

'''
返回到上一级目录，执行：celery worker -A celery_worker.worker -l info
'''

from __future__ import absolute_import

import json
import time
import redis
from celery import Celery, platforms
from celery import states
from jackals.const import TaskStatus
from jackals.settings import CELERY_AMQP_URL, CELERY_BACKEND_URL,WEBSOCKET_REDIS_CHANNEL_URL

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

    MAX_LOST = 5    #允许丢失的heartbeat信号次数
    live_nodes = {}
    
    data_conn = redis.StrictRedis.from_url(CELERY_BACKEND_URL)
    chan_conn = redis.StrictRedis.from_url(WEBSOCKET_REDIS_CHANNEL_URL)
    
    def handle_node_off(host, timestamp):
        print host, "offline"
        node_key = "nodes:%s"%host
        for taskid in data_conn.lrange(node_key, 0, -1):
            #task_id, result, status, traceback=None, request=None, **kwargs
            app.backend.store_result(taskid, None, states.FAILURE) 
            def _down_worker(pipe):
                pipe.multi()
                pipe.hmset(taskid, {
                    "status": TaskStatus.FAILED,
                    "stime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
                }) 
            data_conn.transaction(_down_worker, "task:%s"%taskid)
        data_conn.delete(node_key)
        try:
            del live_nodes[host]
        except KeyError:
            pass
        
    #task-started: uuid, hostname, timestamp, pid
    def task_started(event):
        taskid = event["uuid"]        
        
        data_conn.hmset("task:%s"%taskid, {
            "pid": event["pid"],
            "status": TaskStatus.RUNING,
            "host": event["hostname"],
            "stime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(event["timestamp"]))
        })
        
        data_conn.rpush("nodes:%s"%event["hostname"], taskid)
        
        channel_name = taskid + "_logs"
        chan_conn.publish(channel_name, json.dumps({
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
            data_conn.hmset("task:%s"%taskid, {
                "status": TaskStatus.SUCCESS,
                "ftime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(event["timestamp"]))
            })
            chan_conn.publish(channel_name, json.dumps({
                "type": "STATUS",
                "message": TaskStatus.SUCCESS
            }))
            print "%s succeed"%taskid
        else:
            data_conn.hmset("task:%s"%taskid, {
                "status": TaskStatus.FAILED,
                "ftime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(event["timestamp"]))
            })
            chan_conn.publish(channel_name, json.dumps({
                "type": "STATUS",
                "message": TaskStatus.FAILED
            }))
            print "%s failed!!!"%taskid
            
        data_conn.lrem("nodes:%s"%event["hostname"], taskid)
            
    #task-revoked(uuid, terminated, signum, expired)
    def task_revoked(event):
        taskid = event["uuid"]    
        
        data_conn.hmset("task:%s"%taskid, {
            "status": TaskStatus.KILLED,
            "ftime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        })
        
        channel_name = taskid + "_logs"
        chan_conn.publish(channel_name, json.dumps({
            "type": "STATUS",
            "message": TaskStatus.KILLED
        }))
        print "%s killed!!!"%taskid
        
    #task-failed: uuid, exception, traceback, hostname, timestamp
    def task_failed(event):
        taskid = event["uuid"]    
        
        data_conn.hmset("task:%s"%taskid, {
            "status": TaskStatus.FAILED,
            "stime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(event["timestamp"]))
        })
        
        channel_name = taskid + "_logs"
        chan_conn.publish(channel_name, json.dumps({
            "type": "STATUS",
            "message": TaskStatus.FAILED
        }))
        print "%s failed!!!"%taskid
        data_conn.lrem("nodes:%s"%event["hostname"], taskid, 0)
        
    #hostname, timestamp, freq, sw_ident, sw_ver, sw_sys    
    def worker_offline(event):
        '''
        如果结点所在宿主机突然断电或着所在容器被杀死，
        offline事件不会被检测到，只有celery woker进程退出(被杀死)时才会被检测到
        如果结点掉线了，直接将该结点上的task全部标为失败。
        '''
        handle_node_off(event["hostname"], event["timestamp"])
        
    #hostname, timestamp, freq, sw_ident, sw_ver, sw_sys
    def worker_online(event):
        '''
        新增结点
        '''
        print event["hostname"], "online"
        live_nodes[event["hostname"]] = MAX_LOST
        
    #hostname, timestamp, freq, sw_ident, sw_ver, sw_sys, active, processed
    def worker_heartbeat(event):
        '''
        心跳检测，2秒一次
        '''
        for host in live_nodes:
            live_nodes[host] -= 1
        
        live_nodes[event["hostname"]] = MAX_LOST
        
        for host, times in live_nodes.items():
            if times < 1:
                handle_node_off(host, event["timestamp"])
                                    
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

