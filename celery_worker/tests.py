import unittest
import os
import uuid
from time import sleep
from jackals.celery_worker.tasks import script_worker
from jackals.channels import RedisChannel
import json

class TestSubmitTask(unittest.TestCase):
    
    def setUp(self):
        self.pyname = "/tmp/test_submit_task.py"
        codes = "print 'hello,world'"
        with open(self.pyname, "w") as writer:
            writer.write(codes)
            
    def tearDown(self):
        if os.path.exists(self.pyname):
            os.remove(self.pyname)
    
    def test_submit_task(self):
        taskid = str(uuid.uuid4())
        
        chan = RedisChannel()
        channel_name = taskid+"_logs"
        chan.subscribe(channel_name)
        
        script_worker.apply_async([self.pyname], task_id=taskid)
        
        sleep(0.3)
        
        msg = chan.get_message(channel_name)
        
        if msg:
            msg = json.loads(msg)
          
        self.assertEqual(msg.get("message", None), "hello,world")
        
        
if __name__ == "__main__":
    unittest.main()