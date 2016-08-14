import unittest
import os
from celery_server.app import script_worker
import uuid
from channels import RedisChannel
from time import sleep

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
        
        self.assertEqual(msg, "hello,world")
        
        
if __name__ == "__main__":
    unittest.main()