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
        return self.instr.readReg_float(0x2220, 0x01)
    
    def setVoltage(self, set_v):
        return self.instr.writeReg_float(0x2220, 0x1, set_v);
    
    def getCurrent(self):
        return self.instr.readReg_float(0x2220, 0x02)
    
    def setCurrent(self, set_i):
        return self.instr.writeReg_float(0x2220, 0x2, set_i);
    
    def getPower(self):
        return self.instr.readReg_float(0x2220, 0x03)
    
    def setPower(self, set_p):
        return self.instr.writeReg_float(0x2220, 0x3, set_p);
    
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