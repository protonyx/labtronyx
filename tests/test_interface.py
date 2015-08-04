import unittest
import mock

import labtronyx
from labtronyx.bases import Base_Resource, Base_Interface

class Interface_Tests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.instr = labtronyx.InstrumentManager(rpc=False)

        # Create a fake interface, imitating the interface API
        self.interf = Base_Interface(manager=self.instr)
        self.interf.open = mock.Mock(return_value=True)
        self.interf.close = mock.Mock(return_value=True)

        # Create a fake resource
        self.res = Base_Resource(manager=self.instr,
                                 interface=self.interf,
                                 resID='DEBUG')
        self.res.getProperties = mock.Mock(return_value=dict(resourceID= 'DEBUG'))
        self.interf._resources = {'DEBUG': self.res}

        self.instr._interfaces['interfaces.i_Debug'] = self.interf
        
    def test_resource(self):
        self.dev = self.instr.findInstruments(resourceID='DEBUG')
        self.assertEqual(type(self.dev), list)
        self.assertEqual(len(self.dev), 1)

        self.dev = self.dev[0]
        