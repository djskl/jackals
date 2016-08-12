# coding: utf-8

import marshal
import pickle
import json

import subprocess
from channels import RedisChannel
from celery_server.app import script_worker

class CeleryTask(object):
    
    func = None
        
    def create(self, script_file, *args, **kwargs):
        if script_file.endswith("py"):
            _cmd = ["python", script_file] + [str(arg) for arg in args]
            for k, v in kwargs:
                _cmd.append("-"+k+" "+v)
                
            def _():
                
                chan = RedisChannel()
                chan_name = "LOGS"
                chan.subscribe(chan_name)
                
                p = subprocess.Popen(_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                for line in iter(p.stdout.readline, ""):
                    if line.endswith("\n"):
                        line = line[:-1]
                    chan.publish(chan_name, line)
                     
                for line in iter(p.stderr.readline, ""):
                    if line.endswith("\n"):
                        line = line[:-1]
                    chan.publish(chan_name, line)
                          
            self.func = _
            
            return True
        
        return False
    
    def run(self):
        if self.func:
            func_info = {
                "name": pickle.dumps(self.func.func_name),
                "args": pickle.dumps(self.func.func_defaults),
                "closure": pickle.dumps(self.func.func_closure),
                "code": marshal.dumps(self.func.func_code)
            }
            script_worker.delay(json.dumps(func_info))

if __name__=="__main__":
    ct = CeleryTask()
    ct.create("/root/git/uwsgi-websocket/celery_server/ces.py")
    ct.run()
    


    