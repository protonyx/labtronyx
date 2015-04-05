import unittest

import sys
sys.path.append("..")

from labtronyx import InstrumentManager

class InstrumentManager_Tests(unittest.TestCase):
    
    def setUp(self):
        self.instr = InstrumentManager()
        
    def tearDown(self):
        self.instr.stop()
        
    def test_get_properties(self):
        
        resources = self.instr.getProperties()
        self.assertEqual(type(resources), dict)
        
        for resID, res in resources.items():
            if res.get('resID') == 'DEBUG':
                return True
            
        else:
            return False
        
        