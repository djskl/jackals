import unittest

import marshal
import pickle
import json

from celery_server.app import script_worker

class TestSubmitTask(unittest.TestCase):
    
    def test_submit_task(self):
        
        def f():
            return "hello, world"
        
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