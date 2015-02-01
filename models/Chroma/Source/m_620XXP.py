from models import m_Base

class m_620XXP(m_Base):
    
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