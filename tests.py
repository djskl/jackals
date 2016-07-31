'''
Created on Jul 31, 2016

@author: root
'''
import unittest
from websocket import create_connection
import redis

class Test(unittest.TestCase):

    def setUp(self):
        self._channel = "foobar"
        self.ws_client = create_connection("ws://127.0.0.1/%s"%self._channel)
        self.redis_conn = redis.StrictRedis()
        
    def tearDown(self):
        self.ws_client.close()
        
    def test_ws_send(self):
        msg = "hello"
        length = self.ws_client.send(msg)
        self.assertEqual(length, len(msg)+6)
        
    def test_redis_channel(self):
        self.redis_conn.publish(self._channel, "hello")
        msg = self.ws_client.recv()
        self.assertEquals(msg, "hello")
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()