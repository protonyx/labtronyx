from . import *

class m_BDPC_BR2(Base_ICP.Base_ICP):
    """
    
    """
    
    info = {
        # Model revision author
        'author':               'KKENNEDY',
        # Model version
        'version':              '1.0',
        # Revision date of Model version
        'date':                 '2015-01-31',
        # Device Manufacturer
        'deviceVendor':         'UPEL',
        # List of compatible device models
        'deviceModel':          ['BDPC 2kW Dual-SRC6'],
        # Device type    
        'deviceType':           'DC-DC Converter',      
        
        # List of compatible resource types
        'validResourceTypes':   ['UPEL']
    }
    
    def getProperties(self):
        prop = Base_ICP.Base_ICP.getProperties(self)
        
        prop['deviceVendor'] = 'UPEL'
        prop['deviceModel'] = 'BDPC Dual 2kW'
        
        # Add any additional properties here
        return prop
