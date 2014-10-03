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
    
    #===========================================================================
    # Parameters
    #===========================================================================
    
    def getVoltage(self):
        pass
    
    def setVoltage(self, set_v):
        pass
    
    def getCurrent(self):
        pass
    
    def setCurrent(self, set_i):
        pass
    
    def getPower(self):
        pass
    
    def setPower(self, set_p):
        pass
    
    #===========================================================================
    # Diagnostics
    #===========================================================================
    
    
    
    #===========================================================================
    # Sensor Data
    #===========================================================================
    
    def getPrimaryPower(self):
        pv = self.getSensorValue(1)
        pi = self.getSensorValue(3)
        
        return pv*pi
    
    def getSecondaryPower(self):
        sv = self.getSensorValue(2)
        si = self.getSensorValue(4)
        
        return sv*si
    
    def getConversionRatio(self):
        pv = self.getSensorValue(1) 
        sv = self.getSensorValue(2)
        
        return float(sv) / float(pv)
    
    def getEfficiency(self):
        pp = self.getPrimaryPower()
        sp = self.getSecondaryPower()
        
        return float(sp) / float(pp)
    
    def getSensorValue(self, sensor):
        return self._getRegisterValue_float(0x2122, sensor)
    
    def getSensorType(self, sensor):
        ret = {}
        
        ret['description'] = 'test' # self.readRegisterValue(0x2120, sensorNumber)
        ret['units'] = 'A' # self.readRegisterValue(0x2121, sensorNumber)
        
        return ret