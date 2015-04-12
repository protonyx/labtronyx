import csv
import struct
import sys
import time

import serial
import numpy as np

sys.path.append('..')
from labtronyx import Base_Script

class t_test(Base_Script):
    
    test_info = {
        'name': "Script Template",
        'version': 1.0
    }
    
    def open(self):
        # Tests
        self.registerTest('One', 'test_one')
        self.registerTest('Two', 'test_two')
        
    def test_one(self):
        time.sleep(5.0)
        return True
        
    def test_two(self):
        time.sleep(5.0)
        return True
    
if __name__ == '__main__':
    test = t_test()

