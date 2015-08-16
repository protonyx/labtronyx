import unittest

from labtronyx import InstrumentManager

class InstrumentManager_Init_Tests(unittest.TestCase):

    def test_init_time_no_rpc(self):
        import time
        start = time.clock()
        instr = InstrumentManager(rpc=False)
        delta = time.clock() - start
        self.assertLessEqual(delta, 1.0, "No RPC Init time must be less than 1.0 second(s)")

    def test_init_time_rpc(self):
        import time
        start = time.clock()
        instr = InstrumentManager(rpc=True)
        delta = time.clock() - start
        self.assertLessEqual(delta, 2.0, "RPC Init time must be less than 2.0 second(s)")

        instr.rpc_stop()

class InstrumentManager_Tests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.instr = InstrumentManager(rpc=False)

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
        
        