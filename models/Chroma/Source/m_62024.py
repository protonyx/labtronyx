from models import m_Base

class m_62024(m_Base):
    
    # Model device type
    deviceType = 'Source'
    
    # List of valid Controllers that are compatible with this Model
    validControllers = ['c_VISA']
    
    # List of Valid Vendor Identifier (VID) and Product Identifier (PID) values
    # that are compatible with this Model
    validVIDs = ['Chroma']
    validPIDs = ['62024P-600-8']
    
    def _onLoad(self):
        self._identity = None
        self.controller = self.getControllerObject()
        
        try:
            # Use c_VISA
            self.__instr = self.controller.openResourceObject(self.resID)
            
            resp = self.__instr.ask("*IDN?")
            self._identity = resp.strip().split(',')
            
        except:
            self.logger.exception("Internal error while attaching to VISA instrument")
    
    def _onUnload(self):
        pass
    
    def getProperties(self):
        ret = m_Base.getProperties(self)
        
        ret['deviceVendor'] = 'Chroma'
        if self._identity is not None:
            ret['deviceModel'] = self._identity[1]
            ret['deviceSerial'] = self._identity[3]
            ret['deviceFirmware'] = self._identity[2]
            
        return ret
    
    def powerOn(self):
        self.__instr.write("CONF:OUTP ON")
        
    def powerOff(self):
        self.__instr.write("CONF:OUTP OFF")
        #self.__instr.write("ABORT")
        
    def setVoltage(self, voltage):
        self.__instr.write("SOUR:VOLT %f" % float(voltage))
    
    def setVoltageLimit(self, voltage):
        self.__instr.write("SOUR:VOLT:LIM:HIGH %f" % float(voltage))
        
    def measureVoltage(self):
        return self.__instr.ask("FETC:VOLT?")
    
    def setCurrent(self, current):
        self.__instr.write("SOUR:CURR %f" % float(current))
        
    def setCurrentLimit(self, current):
        self.__instr.write("SOUR:CURR:PROT:HIGH %f" % float(current))
        
    def measureCurrent(self):
        return self.__instr.ask("FETC:CURR?")
    
    def measurePower(self):
        return self.__instr.ask("FETC:POW?")