import unittest

import sys

sys.path.append('..')
import common.rpc as rpc
#from common.rpc.errors import *
#from common.rpc.server import *
#from common.rpc.client import *

class rpc_test_object(object):
    def rpc_test_method_int(self):
        return 1
    
    def rpc_test_method_multi_pos(self, param1, param2):
        if param1 == 1 and param2 == 2:
            return True
        else:
            return False
        
    def rpc_test_method_multi_named(self, **kwargs):
        if kwargs.get('param1') == 1 and kwargs.get('param2') == 2:
            return True
        else:
            return False
        
    def rpc_test_method_multi_combo(self, param1, **kwargs):
        if param1 == 1 and kwargs.get('param2') == 2:
            return True
        else:
            return False
    
    def rpc_test_method_exception(self):
        raise RuntimeError
    
class Json_Rpc_Tests(unittest.TestCase):
    
    def setUp(self):
        self.test_obj = rpc_test_object()
    
    def test_request(self):
        test = rpc.JsonRpcPacket()
        test.addRequest(1, 'test')
        
        requests = test.getRequests()
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].getMethod(), 'test')
        
    def test_request_call_no_params(self):
        test = rpc.JsonRpcPacket()
        test.addRequest(1, 'rpc_test_method_int')
        
        requests = test.getRequests()
        test_req = requests.pop()
        test_ret = test_req.call(self.test_obj.rpc_test_method_int)
        
        self.assertEqual(test_ret, 1)
        
    def test_request_call_multi_pos_param(self):
        test = rpc.JsonRpcPacket()
        test.addRequest(1, 'rpc_test_method_multi_pos', 1, 2)
        
        requests = test.getRequests()
        test_req = requests.pop()
        test_ret = test_req.call(self.test_obj.rpc_test_method_multi_pos)
        
        self.assertTrue(test_ret)
        
    def test_request_call_multi_named_param(self):
        test = rpc.JsonRpcPacket()
        test.addRequest(1, 'rpc_test_method_multi_named', param1=1, param2=2)
        
        requests = test.getRequests()
        test_req = requests.pop()
        test_ret = test_req.call(self.test_obj.rpc_test_method_multi_named)
        
        self.assertTrue(test_ret)
        
    def test_request_call_multi_combo_param(self):
        test = rpc.JsonRpcPacket()
        test.addRequest(1, 'rpc_test_method_multi_combo', 1, param2=2)
        
        requests = test.getRequests()
        test_req = requests.pop()
        test_ret = test_req.call(self.test_obj.rpc_test_method_multi_combo)
        
        self.assertTrue(test_ret)
        
    def test_request_call_exception(self):
        test = rpc.JsonRpcPacket()
        test.addRequest(1, 'rpc_test_method_int')
        
        requests = test.getRequests()
        test_req = requests.pop()
        test_ret = test_req.call(self.test_obj.rpc_test_method_int)
        
        self.assertEqual(test_ret, 1)
    
    def test_decode(self):
        test_str = '{"jsonrpc": "2.0", "method": "test", "params": {}, "id": 1}'
        
        test = rpc.JsonRpcPacket(test_str)
        requests = test.getRequests()
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].getMethod(), 'test')
        
        errors = test.getErrors()
        self.assertEqual(len(errors), 0)
        
    def test_decode_error_invalid_json(self):
        test_str = '{"jsonrpc": "2.0", "method": "foobar, "params": "bar", "baz]'
        
        test = rpc.JsonRpcPacket(test_str)
        requests = test.getRequests()
        self.assertEqual(len(requests), 0)
        
        errors = test.getErrors()
        self.assertEqual(len(errors), 1)
        self.assertEqual(type(errors[0]), rpc.JsonRpc_ParseError)
        
    def test_decode_error_invalid_request(self):
        test_str = '{"jsonrpc": "2.0", "method": 1, "params": "bar"}'
        
        test = rpc.JsonRpcPacket(test_str)
        requests = test.getRequests()
        self.assertEqual(len(requests), 0)
        
        errors = test.getErrors()
        self.assertEqual(len(errors), 1)
        self.assertEqual(type(errors[0]), rpc.JsonRpc_InvalidRequest)
        
    def test_decode_error_parse_empty_request(self):
        test_str = '{}'
        
        test = rpc.JsonRpcPacket(test_str)
        requests = test.getRequests()
        self.assertEqual(len(requests), 0)
        
        errors = test.getErrors()
        self.assertEqual(len(errors), 1)
        self.assertEqual(type(errors[0]), rpc.JsonRpc_InvalidRequest)
        
    def test_decode_error_batch_invalid_json(self):
        test_str = '[\
                        {"jsonrpc": "2.0", "method": "sum", "params": [1,2,4], "id": "1"},\
                        {"jsonrpc": "2.0", "method"\
                    ]'
        
        test = rpc.JsonRpcPacket(test_str)
        requests = test.getRequests()
        self.assertEqual(len(requests), 0)
        
        errors = test.getErrors()
        self.assertEqual(len(errors), 1)
        self.assertEqual(type(errors[0]), rpc.JsonRpc_ParseError)
        
    def test_decode_error_batch_empty(self):
        test_str = '[]'
        
        test = rpc.JsonRpcPacket(test_str)
        requests = test.getRequests()
        self.assertEqual(len(requests), 0)
        
        errors = test.getErrors()
        self.assertEqual(len(errors), 1)
        self.assertEqual(type(errors[0]), rpc.JsonRpc_InvalidRequest)
        
    def test_decode_error_batch_invalid_nonempty(self):
        test_str = '[1]'
        
        test = rpc.JsonRpcPacket(test_str)
        requests = test.getRequests()
        self.assertEqual(len(requests), 0)
        
        errors = test.getErrors()
        self.assertEqual(len(errors), 1)
        self.assertEqual(type(errors[0]), rpc.JsonRpc_InvalidRequest)
        
    def test_decode_error_parse_invalid_batch(self):
        test_str = '[1,2,3]'
        
        test = rpc.JsonRpcPacket(test_str)
        requests = test.getRequests()
        self.assertEqual(len(requests), 0)
        
        errors = test.getErrors()
        self.assertEqual(len(errors), 3)
        self.assertEqual(type(errors[0]), rpc.JsonRpc_InvalidRequest)
        self.assertEqual(type(errors[1]), rpc.JsonRpc_InvalidRequest)
        self.assertEqual(type(errors[2]), rpc.JsonRpc_InvalidRequest)
    
    def test_decode_multi(self):
        test_str = '[{"jsonrpc": "2.0", "method": "test1", "params": {}, "id": 1}, \
                     {"jsonrpc": "2.0", "method": "test2", "params": {}, "id": 2}]'
        
        test = rpc.JsonRpcPacket(test_str)
        requests = test.getRequests()
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0].getMethod(), 'test1')
        
    def test_response(self):
        test = rpc.JsonRpcPacket()
        test.addResponse(1, True)
        
        responses = test.getResponses()
        self.assertEqual(len(responses), 1)
        self.assertEqual(responses[0].getResult(), True)
        