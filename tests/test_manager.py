import unittest

import sys
sys.path.append("..")

class InstrumentManager_Tests(unittest.TestCase):
    
    def setUp(self):
        from InstrumentControl import InstrumentControl
        self.instr = InstrumentControl()
        
    def tearDown(self):
        self.instr.stopManager('localhost')
        
    def test_get_resources(self):
        
        resources = self.instr.getResources()
        self.assertEqual(type(resources), dict)
        
        for resID, res in resources.items():
            if res.get('resID') == 'DEBUG':
                return True
            
        else:
            return False
        
        