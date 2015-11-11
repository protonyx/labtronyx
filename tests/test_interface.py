import unittest
from nose.tools import * # PEP8 asserts
import os

import mock

import labtronyx
from labtronyx.bases import ResourceBase, InterfaceBase

def test_interfaces():
    # Nose test generator to run unittests on discovered interfaces
    instr = labtronyx.InstrumentManager()

    for interName, interCls in instr.plugin_manager.getPluginsByCategory('interfaces').items():
        yield check_interface_api, interCls

def check_interface_api(interfaceCls):
    interfaceCls._validateAttributes()


class Interface_Integration_Tests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.manager = labtronyx.InstrumentManager()

        # Create a fake interface, imitating the interface API
        self.interf = InterfaceBase(manager=self.manager)
        self.interf.open = mock.Mock(return_value=True)
        self.interf.close = mock.Mock(return_value=True)

        # Create a fake resource
        self.res = ResourceBase(manager=self.manager,
                                 interface=self.interf,
                                 resID='DEBUG')
        self.res.getProperties = mock.Mock(return_value=dict(resourceID='DEBUG'))

        # self.interf.resources = {self.res.uuid: self.res}

        # Inject the fake plugins into the manager instance
        self.manager.plugin_manager._plugins_instances[self.interf.uuid] = self.interf
        self.manager.plugin_manager._plugins_instances[self.res.uuid] = self.res

    def setUp(self):
        self.skipTest("Integration tests are broken with new plugin API")
        
    def test_resource(self):
        self.dev = self.manager.findInstruments(resourceID='DEBUG')
        self.assertEqual(type(self.dev), list)
        self.assertEqual(len(self.dev), 1)

        self.dev = self.dev[0]

    def test_interface_get_properties(self):
        self.manager.getProperties()


class VISA_Sim_Tests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Setup a mock manager
        cls.manager = labtronyx.InstrumentManager()

        if 'TRAVIS' in os.environ or cls.manager.interfaces.get('VISA') is None:
            lib_path = os.path.join(os.path.dirname(__file__), 'sim', 'default.yaml')

            cls.manager.enableInterface('VISA', library='%s@sim'%lib_path)

        interfaceInstancesByName = {pluginCls.interfaceName: pluginCls for plugin_uuid, pluginCls
                                    in cls.manager.interfaces.items()}
        cls.i_visa = interfaceInstancesByName.get('VISA')

    def setUp(self):
        if self.i_visa is None:
            self.fail("VISA Interface not enabled")

    def test_enumerate_time(self):
        import time
        start = time.clock()
        self.i_visa.enumerate()
        self.assertLessEqual(time.clock() - start, 1.0, "VISA refresh time must be less than 1.0 second(s)")

    def test_get_resources(self):
        dev_list = self.manager.findInstruments(interface='VISA')
        self.assertGreater(len(dev_list), 0)

    def test_resource_api(self):
        dev_list = self.manager.findInstruments(interface='VISA')
        test_res = dev_list[0]

        # API Checks
        self.check_get_configuration(test_res)
        self.check_ops_error_while_closed(test_res)

    def check_get_configuration(self, test_res):
        # Get configuration
        res_conf = test_res.getConfiguration()
        self.assertEqual(type(res_conf), dict)

    def check_ops_error_while_closed(self, test_res):
        test_res.close()

        with self.assertRaises(labtronyx.ResourceNotOpen):
            test_res.write('BAD')

        with self.assertRaises(labtronyx.ResourceNotOpen):
            test_res.write_raw('BAD')

        with self.assertRaises(labtronyx.ResourceNotOpen):
            test_res.read()

        with self.assertRaises(labtronyx.ResourceNotOpen):
            test_res.read_raw(1)

        with self.assertRaises(labtronyx.ResourceNotOpen):
            test_res.query('BAD?')


class VISA_Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = labtronyx.InstrumentManager()

    def setUp(self):
        if self.manager.interfaces.get('VISA') is None:
            self.skipTest('VISA library not installed')

    def test_enumerate_time(self):
        import time
        start = time.clock()

        i_visa = self.manager.interfaces.get('VISA')
        i_visa.enumerate()

        self.assertLessEqual(time.clock() - start, 1.0, "VISA refresh time must be less than 1.0 second(s)")

    def test_get_resources(self):
        i_visa = self.manager.interfaces.get('VISA')
        ret = i_visa.resources
        self.assertEqual(type(ret), dict)

    def test_get_resource_invalid(self):
        with self.assertRaises(labtronyx.ResourceUnavailable):
            self.manager.getResource('VISA', 'INVALID')


class Serial_Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = labtronyx.InstrumentManager()

    def setUp(self):
        if self.manager.interfaces.get('Serial') is None:
            self.skipTest('Serial library not enabled')

    def test_get_resources(self):
        with self.assertRaises(labtronyx.ResourceUnavailable):
            self.manager.getResource('Serial', 'INVALID')

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