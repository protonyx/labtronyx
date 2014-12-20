from . import *

class m_BDPC_BR2(Base_ICP.Base_ICP):
    """
    
    """
    
    # List of Valid Vendor Identifier (VID) and Product Identifier (PID) values
    # that are compatible with this Model
    validPIDs = ['BDPC_BR2']
    
    def getProperties(self):
        prop = Base_ICP.Base_ICP.getProperties(self)
        
        prop['deviceVendor'] = 'UPEL'
        prop['deviceModel'] = 'BDPC Dual 2kW'
        
        # Add any additional properties here
        return prop
