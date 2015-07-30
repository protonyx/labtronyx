import unittest
import mock

from labtronyx import InstrumentManager
from labtronyx.bases import Base_Resource, Base_Interface

class Resource_Tests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.instr = InstrumentManager(rpc=False)

        # Create a fake resource
        self.res = Base_Resource()

        # Create a fake interface, imitating the interface API
        self.interf = Base_Interface()
        self.interf.open = mock.Mock(return_value=True)
        self.interf.close = mock.Mock(return_value=True)
        self.interf.getResources = mock.Mock(return_value={'DEBUG': self.res})

        self.instr.interfaces['interfaces.i_Debug'] = self.interf
        
    def test_resource_found(self):
        self.dev = self.instr.findInstruments(resourceID='DEBUG')
        self.assertEqual(type(self.dev), list)
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
        
        