import unittest
from nose.tools import * # PEP8 asserts

import labtronyx

def test_init_time_no_rpc():
    import time
    start = time.clock()
    instr = labtronyx.InstrumentManager()
    delta = time.clock() - start
    assert_less_equal(delta, 1.0, "No RPC Init time must be less than 1.0 second(s)")

class InstrumentManager_Tests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.instr = labtronyx.InstrumentManager()

    def test_get_version(self):
        self.assertIsNotNone(self.instr.getVersion())
        
    def test_get_properties(self):
        resources = self.instr.getProperties()
        self.assertEqual(type(resources), dict)
        
        for resID, res in resources.items():
            if res.get('resID') == 'DEBUG':
                return True
            
        return False

    def test_get_hostname(self):
        self.assertIsNotNone(self.instr.getHostname())

    def test_get_address(self):
        self.assertIsNotNone(self.instr.getAddress())

    def test_refresh(self):
        self.instr.refresh()
        
    def test_get_drivers(self):
        self.assertIsNotNone(self.instr.listDrivers())
        self.assertIsNotNone(self.instr.getDriverInfo())

    def test_get_resource(self):
        self.assertRaises(labtronyx.InterfaceUnavailable, self.instr.getResource, 'INVALID', 'NOPE')

    def test_plugins(self):
        bad_plugs = self.instr.plugin_manager.getDisabledPlugins()

        self.assertEqual(len(bad_plugs), 0, "1 or more plugins failed validation")

        plugs = self.instr.plugin_manager.getAllPlugins()

        self.assertGreater(len(plugs), 0, "No plugins were found")

        test_plug = plugs.values()[0]

        self.assertTrue(len(test_plug._getAttributeClasses()) > 0)
        self.assertTrue(len(test_plug.getAttributes()) > 0)