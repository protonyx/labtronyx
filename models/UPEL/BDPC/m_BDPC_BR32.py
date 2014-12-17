from . import m_BDPC_ICP

class m_BDPC_BR32(m_BDPC_ICP):
    """
    
    """
    
    # Model device type
    deviceType = 'Source'
    
    # List of Valid Vendor Identifier (VID) and Product Identifier (PID) values
    # that are compatible with this Model
    validPIDs = ['BDPC_BR32']
    
    def getProperties(self):
        prop = m_BDPC.getProperties(self)
        
        prop['deviceVendor'] = 'UPEL'
        prop['deviceModel'] = 'BDPC 32kW'
        
        return prop
    
    def getSensorValue(self, sensor):
        return self._getRegisterValue(0x2122, sensor)    
