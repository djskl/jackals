'''
Created on Jul 31, 2016

@author: root
'''
import unittest
from websocket_server.tests import TestWebsocket
from celery_worker.tests import TestSubmitTask
        
if __name__ == "__main__":
    suite1 = unittest.TestLoader().loadTestsFromTestCase(TestWebsocket)
    suite2 = unittest.TestLoader().loadTestsFromTestCase(TestSubmitTask)
    alltests = unittest.TestSuite([suite1, suite2])
    unittest.TextTestRunner(verbosity=2).run(alltests)
    
    