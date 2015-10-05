import unittest
from nose.tools import * # PEP8 asserts

import labtronyx

labtronyx.logConsole()

def test_init_time_no_rpc():
    import time
    start = time.clock()
    instr = labtronyx.InstrumentManager(rpc=False)
    delta = time.clock() - start
    assert_less_equal(delta, 1.0, "No RPC Init time must be less than 1.0 second(s)")

class InstrumentManager_Tests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.instr = labtronyx.InstrumentManager(rpc=False)

    def test_get_version(self):
        self.assertIsNotNone(self.instr.getVersion())
        
    def test_get_properties(self):
        resources = self.instr.getProperties()
        self.assertEqual(type(resources), dict)
        
        for resID, res in resources.items():
            if res.get('resID') == 'DEBUG':
                return True
            
        else:
            return False

    def test_refresh(self):
        self.instr.refresh()
        
        