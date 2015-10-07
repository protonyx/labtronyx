import unittest
from nose.tools import * # PEP8 asserts
import os

import mock

import labtronyx
from labtronyx.bases import Base_Resource, Base_Interface

def test_interfaces():
    # Nose test generator to run unittests on discovered interfaces
    instr = labtronyx.InstrumentManager(rpc=False)

    for interName, interCls in instr.interfaces.items():
        yield check_interface_api, interCls

def check_interface_api(interfaceCls):
    assert_true(hasattr(interfaceCls, 'info'))

class Interface_Integration_Tests(unittest.TestCase):

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

        # Inject the resource into the fake interface
        self.interf._resources = {'DEBUG': self.res}

        # Inject the fake interface into the manager instance
        self.instr._interfaces['interfaces.i_Debug'] = self.interf
        
    def test_resource(self):
        self.dev = self.instr.findInstruments(resourceID='DEBUG')
        self.assertEqual(type(self.dev), list)
        self.assertEqual(len(self.dev), 1)

        self.dev = self.dev[0]

class Interface_VISA_Tests(unittest.TestCase):

    SIM = True

    @classmethod
    def setUpClass(cls):
        # Setup a mock manager
        cls.manager = labtronyx.InstrumentManager(rpc=False)

        if 'TRAVIS' in os.environ or cls.SIM:
            lib_path = os.path.join(os.path.dirname(__file__), 'sim', 'default.yaml')

            cls.manager.enableInterface('VISA', library='%s@sim'%lib_path)

        cls.i_visa = cls.manager._getInterface('VISA')

    def test_interface_visa_enumerate_time(self):
        import time
        start = time.clock()
        self.i_visa.enumerate()
        self.assertLessEqual(time.clock() - start, 1.0, "VISA refresh time must be less than 1.0 second(s)")

    def test_interface_visa_get_resources(self):
        ret = self.i_visa.getResources()

        self.assertEqual(type(ret), dict)

    def test_interface_find_instruments(self):
        dev_list = self.manager.findInstruments()
        self.assertGreater(len(dev_list), 0)

    def test_interface_get_properties(self):
        self.manager.getProperties()