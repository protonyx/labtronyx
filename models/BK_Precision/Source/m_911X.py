import models

class m_911X(models.m_Base):
    
    # Model device type
    deviceType = 'Source'
    
    # List of valid Controllers that are compatible with this Model
    validControllers = ['c_VISA', 'c_Serial']
    
    # List of Valid Vendor Identifier (VID) and Product Identifier (PID) values
    # that are compatible with this Model
    validVIDs = ['BK Precision', 'Unknown']
    validPIDs = ['BK9116']
    
    def _onLoad(self):
        self.__identity = None
        
        try:
            # Use c_VISA
            self.__instr = self.controller._getInstrument(self.resID)
            
            resp = self.__instr.ask("*IDN?")
            self.__identity = resp.strip().split(',')
            
            # Set the instrument into Remote mode
            self.__instr.write("SYS:REM")
            
        except:
            self.logger.exception("Internal error while attaching to VISA instrument")
    
    def _onUnload(self):
        pass
    
    def getProperties(self):
        ret = m_Base.getProperties(self)
        
        ret['deviceVendor'] = 'Agilent'
        if self.__identity is not None:
            ret['deviceModel'] = self.__identity[1]
            ret['deviceSerial'] = self.__identity[2]
            ret['deviceFirmware'] = self.__identity[3]
            
        return ret
    
    def powerOn(self):
        self.__instr.write("SOUR:OUTP:STAT ON")
        
    def powerOff(self):
        self.__instr.write("SOUR:OUTP:STAT OFF")
        
    def setVoltage(self, voltage):
        self.__instr.write("SOUR:VOLT:LEV:IMM:AMPL %f")
        
    def measureVoltage(self):
        return self.__instr.ask("MEAS:VOLT?")
    
    def setCurrent(self, current):
        self.__instr.write("SOUR:CURR:LEV:IMM:AMPL %f" % float(current))
        
    def measureCurrent(self):
        return self.__instr.ask("MEAS:CURR?")
    
    def measurePower(self):
        return self.__instr.ask("MEAS:POW?")
    
    def setVoltageLimit(self, voltage):
        self.__instr.write("SOUR:VOLT:LIM:LEV %f" % float(voltage))
        
    def clearVoltageLimit(self):
        self.__instr.write("SOUR:VOLT:PROT:STAT OFF")
        
    def setOVPLimit(self, voltage):
        self.__instr.write("SOUR:VOLT:PROT:LEV %f" % float(voltage))
        self.__instr.write("SOUR:VOLT:PROT:STAT ON")
        
    def removeOVPLimit(self):
        self.__instr.write("SOUR:VOLT:PROT:STAT OFF")
        
    def clearOVPWarning(self):
        self.__instr.write("PROT:CLE")
    
    