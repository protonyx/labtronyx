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
    
    def getPrimaryPower(self):
        pv = self.getSensorValue(1)
        pi = self.getSensorValue(2)
        
        return pv*pi
    
    def getSecondaryPower(self):
        sv = self.getSensorValue(3)
        si = self.getSensorValue(4)
        
        return sv*si
    
    def getConversionRatio(self):
        pass
    
    def getSensorValue(self, sensor):
        return self._getRegisterValue(0x2122, sensor)
    
    def getSensorType(self, sensor):
        ret = {}
        
        ret['description'] = 'test' # self.readRegisterValue(0x2120, sensorNumber)
        ret['units'] = 'A' # self.readRegisterValue(0x2121, sensorNumber)
        
        return ret