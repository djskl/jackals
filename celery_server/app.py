from celery import Celery, platforms
from celery.utils.log import get_task_logger

app = Celery('ctasks')

app.conf.update(
    BROKER_URL = 'redis://localhost:6379/0',
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/1',
    CELERY_TASK_SERIALIZER = 'json',
    CELERY_RESULT_SERIALIZER = 'json',
    CELERY_ACCEPT_CONTENT=['json']
                  
)

platforms.C_FORCE_ROOT = True

logger = get_task_logger(__name__)

@app.task(name="celery_server.app.add")
def add(x, y):
    return x + y

import subprocess
import redis
@app.task(bind=True, name="celery_server.app.script_worker")
def script_worker(self, script_file, *args, **kwargs):
    if script_file.endswith("pyc"):
        script_file = script_file[:-1]
    
    if not script_file.endswith("py"):
        return None
    
    taskid = self.request.id

#     taskid = "123456"
     
    _cmd = ["python", "-u", script_file] + [str(arg) for arg in args]
    for k, v in kwargs:
        _cmd.append("-"+k+" "+v)
        
    p = subprocess.Popen(_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    conn = redis.StrictRedis()
    
    channel_name = taskid + "_logs"
    
    print "channel_name", channel_name
    
    logger.info("channel_name: %s"%channel_name)
    
    logger.info("start...")
    
    for line in iter(p.stdout.readline, ""):
        if line.endswith("\n"):
            line = line[:-1]
        conn.publish(channel_name, line)
        logger.info(line)
     
    for line in iter(p.stderr.readline, ""):
        if line.endswith("\n"):
            line = line[:-1]
        conn.publish(channel_name, line)
        logger.info(line)

    logger.info("finish!!!")
    
    
    