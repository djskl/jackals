'''
Created on Jul 31, 2016

@author: root
'''
import unittest
from websocket import create_connection
import redis
from utils import make_channel

class Test(unittest.TestCase):

    def setUp(self):
        self.path_info = "foobar"
        self.ws_client = create_connection("ws://127.0.0.1/%s"%self.path_info)
        self.redis_conn = redis.StrictRedis()
        
    def tearDown(self):
        self.ws_client.close()
        
    def test_ws_send(self):
        msg = "hello"
        length = self.ws_client.send(msg)
        self.assertEqual(length, len(msg)+6)
        
    def test_redis_channel(self):
        self._channel = make_channel(self.path_info)
        self.redis_conn.publish(self._channel, "hello")
                
        msg = self.ws_client.recv() # TODO: timeout
        
        self.assertEquals(msg, "hello")
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    
    