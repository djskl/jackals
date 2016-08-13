import unittest

import marshal
import pickle
import json

from celery_server.app import script_worker

class TestSubmitTask(unittest.TestCase):
    
    def test_submit_task(self):
        
        def f():
            import subprocess
            p1 = subprocess.Popen(["ls", "-l", "/tmp/"], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(["wc", "-l"], stdin=p1.stdout, stdout=subprocess.PIPE)
            
            outs, errs = p2.communicate()
            
            return outs
        
        func_info = {
            "name": pickle.dumps(f.func_name),
            "args": pickle.dumps(f.func_defaults),
            "closure": pickle.dumps(f.func_closure),
            "code": marshal.dumps(f.func_code)
        }
        
        rst = script_worker.delay(json.dumps(func_info))
        
        msg = rst.get(timeout=10)
        
        self.assertEqual(msg, "hello, world")
        
if __name__ == "__main__":
    unittest.main()       
    
     