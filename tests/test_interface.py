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

class VISA_Tests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Setup a mock manager
        cls.manager = labtronyx.InstrumentManager(rpc=False)

        if 'TRAVIS' in os.environ or cls.manager._getInterface('VISA') is None:
            lib_path = os.path.join(os.path.dirname(__file__), 'sim', 'default.yaml')

            cls.manager.enableInterface('VISA', library='%s@sim'%lib_path)

        cls.i_visa = cls.manager._getInterface('VISA')

    def test_interface_visa_enumerate_time(self):
        import time
        start = time.clock()
        self.i_visa.enumerate()
        self.assertLessEqual(time.clock() - start, 1.0, "VISA refresh time must be less than 1.0 second(s)")

    def test_interface_open(self):
        self.assertIsNotNone(self.manager._getInterface('VISA'))

    def test_interface_visa_get_resources(self):
        ret = self.i_visa.resources
        self.assertEqual(type(ret), dict)

        self.assertRaises(labtronyx.errors.ResourceUnavailable, self.manager.getResource, 'VISA', 'INVALID')

    def test_interface_find_instruments(self):
        dev_list = self.manager.findInstruments(interface='VISA')
        self.assertGreater(len(dev_list), 0)

    def test_interface_get_properties(self):
        self.manager.getProperties()

class Serial_Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = labtronyx.InstrumentManager(rpc=False)

    def setUp(self):
        if self.manager._getInterface('Serial') is None:
            self.skipTest('Serial library not installed')

    def test_interface_open(self):
        self.assertIsNotNone(self.manager._getInterface('Serial'))

    def test_get_resources(self):
        self.assertRaises(labtronyx.errors.ResourceUnavailable, self.manager.getResource, 'Serial', 'INVALID')

    def test_open_resource(self):
        res_list = self.manager.findResources(interface='Serial')

        if len(res_list) == 0:
            self.skipTest("No serial resources found")

        test_res = res_list[0]

        test_res.open()
        self.assertTrue(test_res.isOpen())

        test_res.close()
        self.assertFalse(test_res.isOpen())

    def test_configure(self):
        res_list = self.manager.findResources(interface='Serial')

        if len(res_list) == 0:
            self.skipTest("No serial resources found")

        test_res = res_list[0]

        conf = dict(
            baud_rate=9600,
            data_bits=8,
            parity='N',
            stop_bits=1,
            write_termination='\n',
            timeout=0.5
        )

        test_res.configure(**conf)

        self.assertDictContainsSubset(conf, test_res.getConfiguration())