from Base_Driver import Base_Driver

class m_620XXP(Base_Driver):
    
    info = {
        # Model revision author
        'author':               'KKENNEDY',
        # Model version
        'version':              '1.0',
        # Revision date of Model version
        'date':                 '2015-01-31',
        # Device Manufacturer
        'deviceVendor':         'Chroma',
        # List of compatible device models
        'deviceModel':          ['62006P-30-80', '62006P-100-25', '62006P-300-8',
                                 '62012P-40-120', '62012P-80-60', '62012P-100-50', '62012P-600-8',
                                 '62024P-40-120', '62024P-80-60', '62024P-100-50', '62024-600-8',
                                 '62052P-100-100'],
        # Device type    
        'deviceType':           'Power Supply',      
        
        # List of compatible resource types
        'validResourceTypes':   ['VISA'],  
        
        #=======================================================================
        # VISA Attributes        
        #=======================================================================
        # Compatible VISA Manufacturers
        'VISA_compatibleManufacturers': ['CHROMA', 'Chroma'],
        # Compatible VISA Models
        'VISA_compatibleModels':        ['62006P-30-80', '62006P-100-25', 
                                         '62006P-300-8', '62012P-40-120', 
                                         '62012P-80-60', '62012P-100-50', 
                                         '62012P-600-8', '62024P-40-120', 
                                         '62024P-80-60', '62024P-100-50', 
                                         '62024-600-8', '62052P-100-100']
    }
    
    def _onLoad(self):
        self.instr = self.getResource()
        
        self.setRemoteControl()
    
    def _onUnload(self):
        self.setLocalControl()
    
    def setRemoteControl(self):
        """
        Sets the load to remote control
        """
        self.instr.write("CONF:REM ON")
    
    def setLocalControl(self):
        """
        Sets the load to local control
        """
        self.instr.write("CONF:REM OFF")
    
    def powerOn(self):
        self.instr.write("CONF:OUTP ON")
        
    def powerOff(self):
        self.instr.write("CONF:OUTP OFF")
        #self.instr.write("ABORT")
        
    def setMeasurementSpeed(self, speed):
        """
        Set the reading speed of the voltage/current sensor
        
        :param speed: Samples per second (one of: 30, 60, 120, 240)
        :type speed: int
        """
        valid_speed = {30: 3,
                       60: 2,
                       120: 1,
                       240: 0}
        if speed in valid_speed:
            self.instr.write("CONF:MEAS:SP %i" % valid_speed.get(speed))
            
        else:
            raise ValueError("Invalid parameter")
        
    def setVoltage(self, voltage):
        self.instr.write("SOUR:VOLT %f" % float(voltage))
    
    def setVoltageLimit(self, voltage):
        self.instr.write("SOUR:VOLT:LIM:HIGH %f" % float(voltage))
        
    def measureVoltage(self):
        return self.instr.ask("FETC:VOLT?")
    
    def setCurrent(self, current):
        self.instr.write("SOUR:CURR %f" % float(current))
        
    def setCurrentLimit(self, current):
        self.instr.write("SOUR:CURR:PROT:HIGH %f" % float(current))
        
    def measureCurrent(self):
        return self.instr.ask("FETC:CURR?")
    
    def measurePower(self):
        return self.instr.ask("FETC:POW?")