import unittest

import time
import sys
sys.path.append("..")

import labtronyx.common.resource_status as resource_status
import labtronyx.common.rpc.errors as rpc_errors

class Resource_Tests(unittest.TestCase):
    
    def setUp(self):
        from labtronyx import InstrumentControl
        self.instr = InstrumentControl(debug=True)
        self.instr.addManager('localhost')
        
    def tearDown(self):
        self.instr.stopManager('localhost')
        
    def test_resource_found(self):
        self.dev = self.instr.findInstrument(resourceID='DEBUG')
        self.assertTrue(len(self.dev) == 1)
        
    def test_resource_init(self):
        self.dev = self.instr.findInstrument(resourceID='DEBUG')
        self.dev[0].open()
        self.assertEqual(self.dev[0].getResourceStatus(), 'READY')
        
    def test_resource_error(self):
        self.dev = self.instr.findInstrument(resourceID='DEBUG')
        self.dev[0].open()
        
        self.dev[0].triggerError()
        
        with self.assertRaises(rpc_errors.RpcServerException):
        
            self.dev[0].write('test')
        
        