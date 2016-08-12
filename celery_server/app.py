from celery import Celery, platforms

app = Celery('ctasks')

app.conf.update(
    BROKER_URL = 'redis://localhost:6379/0',
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/1',
    CELERY_TASK_SERIALIZER = 'json',
    CELERY_RESULT_SERIALIZER = 'json',
    CELERY_ACCEPT_CONTENT=['json']
                  
)

platforms.C_FORCE_ROOT = True

@app.task(name="celery_server.app.add")
def add(x, y):
    return x + y

import marshal
import pickle
import json
import types

@app.task(name="celery_server.app.script_worker")
def script_worker(funcs):
    
    f_obj = json.loads(funcs)
    
    f = types.FunctionType(
        marshal.loads(f_obj["code"]),
        globals(),
        pickle.loads(f_obj["name"]),
        pickle.loads(f_obj["args"]),
        pickle.loads(f_obj["closure"])
    )
    
    return f()
    

