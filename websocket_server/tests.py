import unittest
import redis
from websocket import create_connection

class TestWebsocket(unittest.TestCase):

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
        self.redis_conn.publish("foobar_logs", "hello")
                
        msg = self.ws_client.recv() # TODO: timeout
        
        self.assertEquals(msg, "hello")

        
if __name__ == "__main__":
    unittest.main()    