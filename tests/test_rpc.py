import unittest

import logging
import sys
sys.path.append('..')
from common.rpc.server import *
from common.rpc.client import *

class RPC_Server_Tests(unittest.TestCase):
    
    def test___init__(self):
        srv = RpcServer()
        srv.rpc_stop()
        
class RPC_Client_Tests(unittest.TestCase):
    
    def setUp(self):
        self.srv = RpcServer(port=6780)
        
    def tearDown(self):
        self.srv.rpc_stop()
    
    def test_connect(self):
        client = RpcClient(address='localhost', port=6780)
    
    def test_connect_error_no_server_running(self):
        client = RpcClient(address='localhost', port=6781)