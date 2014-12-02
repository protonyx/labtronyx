import sys
from __builtin__ import NotImplementedError
sys.path.append('.')

from t_Base import t_Base

class t_Template(t_Base):
    
    test_info = {
        'name': "Test Template",
        'version': 1.0
    }
    
    test_requires = [
        
    ]
    
    test_details = {
        'test_testFunction': {
            'name': 'Default Test Function',
            'order': 1 }
    }
    
    def open(self):
        raise NotImplementedError
    
    def close(self):
        raise NotImplementedError
    
    def test_testFunction(self):
        pass