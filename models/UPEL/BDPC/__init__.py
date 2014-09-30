from .. import m_Generic

class m_BDPC(m_Generic):
    """
    Common model for all BDPC devices
    """
    
    # Model device type
    deviceType = 'Source'
    
    def getProperties(self):
        prop = m_Generic.getProperties(self)
        
        # Add any additional properties here
        return prop
    
    def getSensorValue(self, sensor):
        return self._getRegisterValue(0x2122, sensor)