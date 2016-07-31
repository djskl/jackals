'''
Created on Jul 31, 2016

@author: root
'''
import unittest
from websocket import create_connection

class Test(unittest.TestCase):

    def setUp(self):
        self.ws = create_connection("ws://127.0.0.1/foobar")

    def tearDown(self):
        pass


    def testName(self):
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()