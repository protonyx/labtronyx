from Base_Driver import Base_Driver

class m_911X(Base_Driver):
    
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
        self.instr = self.getResource()
        
        self.setRemoteControl()
    
    def _onUnload(self):
        pass
    
    def setRemoteControl(self):
        self.instr.write("SYS:REM")
    
    def powerOn(self):
        self.instr.write("SOUR:OUTP:STAT ON")
        
    def powerOff(self):
        self.instr.write("SOUR:OUTP:STAT OFF")
        
    def setVoltage(self, voltage):
        self.instr.write("SOUR:VOLT:LEV:IMM:AMPL %f" % float(voltage))
        
    def measureVoltage(self):
        return self.instr.ask("MEAS:VOLT?")
    
    def setCurrent(self, current):
        self.instr.write("SOUR:CURR:LEV:IMM:AMPL %f" % float(current))
        
    def measureCurrent(self):
        return self.instr.ask("MEAS:CURR?")
    
    def measurePower(self):
        return self.instr.ask("MEAS:POW?")
    
    def setVoltageLimit(self, voltage):
        self.instr.write("SOUR:VOLT:LIM:LEV %f" % float(voltage))
        
    def clearVoltageLimit(self):
        self.instr.write("SOUR:VOLT:PROT:STAT OFF")
        
    def setOVPLimit(self, voltage):
        self.instr.write("SOUR:VOLT:PROT:LEV %f" % float(voltage))
        self.instr.write("SOUR:VOLT:PROT:STAT ON")
        
    def removeOVPLimit(self):
        self.instr.write("SOUR:VOLT:PROT:STAT OFF")
        
    def clearOVPWarning(self):
        self.instr.write("PROT:CLE")
    
    