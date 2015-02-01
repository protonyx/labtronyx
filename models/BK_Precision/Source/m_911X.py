import models

class m_911X(models.m_Base):
    
    info = {
        # Model revision author
        'author':               'KKENNEDY',
        # Model version
        'version':              '1.0',
        # Revision date of Model version
        'date':                 '2015-01-31',
        # Device Manufacturer
        'deviceVendor':         'BK Precision',
        # List of compatible device models
        'deviceModel':          ['9115', '9116'],
        # Device type    
        'deviceType':           'Power Supply',      
        
        # List of compatible resource types
        'validResourceTypes':   ['VISA'],  
        
        #=======================================================================
        # VISA Attributes        
        #=======================================================================
        # Compatible VISA Manufacturers
        'VISA_compatibleManufacturers': ['BK Precision'],
        # Compatible VISA Models
        'VISA_compatibleModels':        ['BK9115', 'BK9116']
    }
    
    def _onLoad(self):
        self.__identity = None
        self.controller = self.getControllerObject()
        
        try:
            # Use c_VISA
            self.__instr = self.controller.openResourceObject(self.resID)
            
            resp = self.__instr.ask("*IDN?")
            self.__identity = resp.strip().split(',')
            
            # Set the instrument into Remote mode
            self.__instr.write("SYS:REM")
            
        except:
            self.logger.exception("Internal error while attaching to VISA instrument")
    
    def _onUnload(self):
        pass
    
    def getProperties(self):
        ret = models.m_Base.getProperties(self)
        
        ret['deviceVendor'] = 'BK Precision'
        if self.__identity is not None:
            ret['deviceModel'] = self.__identity[1].strip()
            ret['deviceSerial'] = self.__identity[2].strip()
            ret['deviceFirmware'] = self.__identity[3].strip()
            
        return ret
    
    def powerOn(self):
        self.__instr.write("SOUR:OUTP:STAT ON")
        
    def powerOff(self):
        self.__instr.write("SOUR:OUTP:STAT OFF")
        
    def setVoltage(self, voltage):
        self.__instr.write("SOUR:VOLT:LEV:IMM:AMPL %f" % float(voltage))
        
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
    
    