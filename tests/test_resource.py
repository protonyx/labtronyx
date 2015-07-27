import unittest

from labtronyx import InstrumentManager
import labtronyx.common.resource_status as resource_status

class Resource_Tests(unittest.TestCase):
    
    def setUp(self):
        self.instr = InstrumentManager()
        
    def tearDown(self):
        self.instr.stop()
        
    def test_resource_found(self):
        self.dev = self.instr.findInstruments(resourceID='DEBUG')
        self.assertTrue(len(self.dev) == 1)
        
    def test_resource_init(self):
        self.dev = self.instr.findInstruments(resourceID='DEBUG')
        self.dev[0].open()
        self.assertEqual(self.dev[0].getResourceStatus(), 'READY')
        
    def test_resource_error(self):
        self.dev = self.instr.findInstruments(resourceID='DEBUG')
        self.dev[0].open()
        
        self.dev[0].triggerError()
        
        with self.assertRaises(rpc_errors.RpcServerException):
        
            self.dev[0].write('test')
        
        