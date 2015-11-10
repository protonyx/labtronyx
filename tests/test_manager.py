import unittest
from nose.tools import * # PEP8 asserts
import time
import labtronyx


def setUpModule():
    global instr
    instr = labtronyx.InstrumentManager()


def test_plugins():
    for plugin_fqn, plugCls in instr.plugin_manager.plugins.items():
        yield check_plugin, plugCls


def check_plugin(pluginCls):
    # Validate plugin
    assert_true(pluginCls._validateAttributes())

    assert_greater(len(pluginCls._getPluginAttributeClasses()), 0)
    assert_greater(len(pluginCls.getAttributes()), 0)


class InstrumentManager_Tests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        start = time.clock()
        cls.instr = labtronyx.InstrumentManager()
        cls.init_delta = time.clock() - start

    @classmethod
    def tearDownClass(cls):
        cls.instr._close()

    def test_init_time(self):
        assert_less_equal(self.init_delta, 1.0, "No RPC Init time must be less than 1.0 second(s)")

    def test_get_version(self):
        self.assertIsNotNone(self.instr.getVersion())

    def test_get_properties(self):
        resources = self.instr.getProperties()
        self.assertEqual(type(resources), dict)

    def test_get_attributes(self):
        plugins = self.instr.getAttributes()
        self.assertEqual(type(plugins), dict)

    def test_get_hostname(self):
        self.assertIsNotNone(self.instr.getHostname())

    def test_get_address(self):
        self.assertIsNotNone(self.instr.getAddress())

    def test_refresh(self):
        self.instr.refresh()
        
    def test_get_drivers(self):
        self.assertIsNotNone(self.instr.listDrivers())

    def test_get_resource(self):
        self.assertRaises(labtronyx.InterfaceUnavailable, self.instr.getResource, 'INVALID', 'NOPE')

    def test_disable_interface(self):
        self.instr.disableInterface('Serial')
        self.assertNotIn('Serial', self.instr.listInterfaces())

        self.instr.enableInterface('Serial')
        self.assertIn('Serial', self.instr.listInterfaces())