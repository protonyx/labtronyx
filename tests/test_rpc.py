import unittest

import logging
import sys
import time

sys.path.append('..')
import labtronyx.common.rpc as rpc
#from common.rpc.errors import *
#from common.rpc.server import *
#from common.rpc.client import *

class ObjTest1(object):
    def test1(self):
        return 1
    
class ObjTest2(object):
    def test2(self):
        return 2
    
    def test_exception(self):
        raise RuntimeError
    
class RPC_Server_Tests(unittest.TestCase):
    def test_server_init(self):
        self.srv = rpc.RpcServer()
        
        self.srv.rpc_stop()
        
    def test_server_error_already_running(self):
        self.srv = rpc.RpcServer(port=6780)
        
        self.assertRaises(rpc.RpcServerPortInUse, rpc.RpcServer, port=6780)
        
        self.srv.rpc_stop()
        

class RPC_Server_Object_Tests(unittest.TestCase):
    
    def setUp(self):
        self.srv = rpc.RpcServer(port=6780)
        
    def tearDown(self):
        self.srv.rpc_stop()
    
    def test_object_registration(self):
        t1 = ObjTest1()
        t2 = ObjTest2()
        self.srv.registerObject(t1)
        self.srv.registerObject(t2)
        
        methods = self.srv.rpc_getMethods()
        
        self.assertTrue('test1' in methods)
        self.assertTrue('test2' in methods)
        
        method1 = self.srv.findMethod('test1')
        self.assertEqual(method1(), 1)
        
        method2 = self.srv.findMethod('test2')
        self.assertEqual(method2(), 2)
        
        
class RPC_Client_Connection_Tests(unittest.TestCase):
    
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        
        try:
            self.srv = rpc.RpcServer(port=6780)
            
        except rpc.RpcServerPortInUse:
            #client = rpc.RpcClient(address='localhost', port=6780)
            #client.rpc_stop()
            #del client
            
            #self.srv = rpc.RpcServer(port=6780)
            pass
            
        time.sleep(1.0)
        
    def tearDown(self):
        self.srv.rpc_stop()
    
    def test_connect(self):
        client = rpc.RpcClient(address='localhost', port=6780)
        
    def test_connect_error_no_server_running(self):
        """
        Expected Failure: RpcServerNotFound
        """
        self.assertRaises(rpc.RpcServerNotFound, rpc.RpcClient, address='localhost', port=6781)
        
    def test_connect_error_server_restarted(self):
        """
        Stop and start the server while a connection is active and verify
        that it recovers
        """
        client = rpc.RpcClient(address='localhost', port=6780)
        
        self.srv.rpc_stop()
        time.sleep(1.0)
        
        self.srv = rpc.RpcServer(port=6780)
        t1 = ObjTest1()
        self.srv.registerObject(t1)
        
        self.assertEqual(client.test1(), 1)
        #self.assertRaises(rpc.RpcServerNotFound, rpc.RpcClient, address='localhost', port=6780)
        
class RPC_Client_Method_Tests(unittest.TestCase):
    
    def setUp(self):
        self.srv = rpc.RpcServer(port=6780)
        t1 = ObjTest1()
        t2 = ObjTest2()
        self.srv.registerObject(t1)
        self.srv.registerObject(t2)
        self.client = rpc.RpcClient(address='localhost', port=6780)
        
    def tearDown(self):
        self.srv.rpc_stop()
        
    def test_get_methods(self):
        methods = self.client.rpc_getMethods()
        
        self.assertTrue('test1' in methods)
        
    def test_method_call(self):
        self.assertEqual(self.client.test1(), 1)
        self.assertEqual(self.client.test2(), 2)
        
    def test_method_call_error_protected(self):
        with self.assertRaises(rpc.RpcMethodNotFound):
            self.client._rpcCall('_test3')
    
    def test_method_call_error_not_found(self):
        with self.assertRaises(rpc.RpcMethodNotFound):
            self.client._rpcCall('test3')
        
    def test_method_call_error_exception(self):
        with self.assertRaises(rpc.RpcServerException):
            self.client.test_exception()
            
    def test_notification(self):
        import threading
        testVar = threading.Event()
        testVar.clear()
        
        self.client._enableNotifications()
        self.client._registerCallback('NOTIFICATION_TEST', lambda: testVar.set())
        
        self.srv.notifyClients('NOTIFICATION_TEST')
        
        self.client._checkNotifications()
        
        self.assertTrue(testVar.is_set())
  