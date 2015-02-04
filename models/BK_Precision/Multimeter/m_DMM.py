import models
import time

class m_DMM(models.m_Base):
    
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
        'deviceModel':          ['2831E', '5491B', '5492BGPIB', '5492B'],
        # Device type    
        'deviceType':           'Multimeter',      
        
        # List of compatible resource types
        'validResourceTypes':   ['VISA'],  
        
        #=======================================================================
        # VISA Attributes        
        #=======================================================================
        # Compatible VISA Manufacturers
        'VISA_compatibleManufacturers': [''],
        # Compatible VISA Models
        'VISA_compatibleModels':        ['2831E  Multimeter', 
                                         '5491B Digital Multimeter',
                                         '5492B Digital Multimeter']
    }
    
    def _onLoad(self):
        self.instr = self.getResource()
    
    def _onUnload(self):
        pass
    
    def _BK_ask(self, command):
        resp = str(self.instr.ask(command))
        self.logger.debug(resp)
        
        # Check that the SCPI header was not retuned
        ind = resp.find(command)
        if ind != -1:
            ind = ind + len(command)
            resp = resp[ind:]
            
        return resp
    
    def reset(self):
        self.instr.write("*RST")
        
    def getError(self):
        resp = self._BK_ask(":SYST:ERR?")
        return resp

    def getFunction(self):
        return self._BK_ask("FUNC?")

    def setFunction(self, func):
        self.func = func
        self.instr.write(":FUNC %s" % self.func)
    
    def setFunction_DC_Voltage(self):
        self.setFunction("VOLT:DC")
        
    def setFunction_AC_Voltage(self):
        self.setFunction("VOLT:AC")
        
    def setFunction_DC_Current(self):
        self.setFunction("CURR:DC")
        
    def setFunction_AC_Current(self):
        self.setFunction("CURR:AC")
        
    def setFunction_Resistance(self):
        self.setFunction("RES")
        
    def setFunction_Frequency(self):
        self.setFunction("FREQ")
        
    def setFunction_Period(self):
        self.setFunction("PER")
        
    def setFunction_Diode(self):
        self.setFunction("DIOD")
        
    def setFunction_Continuity(self):
        self.setFunction("CONT")

    def getRange(self):
        cmd = self.func + ":RANG?"
        range_raw = self._BK_ask(cmd)
        self.logger.debug("Range: %s" % str(range_raw))
        
    def setRange_Manual(self):
        cmd = self.func + ":RANG:AUTO OFF"
        self.logger.debug(cmd)
        self.instr.write(cmd)
        
    def setRange_Auto(self):
        cmd = self.func + ":RANG:AUTO ON"
        self.logger.debug(cmd)
        self.instr.write(cmd)

    def setRange(self, new_range):
        cmd = self.func + ":RANG " + str(new_range)
        
        self.logger.debug(cmd)
        self.instr.write(cmd)
        
    def getMeasurement(self):
        # Attempt three times to get a measurement
        for x in range(3):
            try:
                meas_raw = self._BK_ask("FETC?")
                self.logger.debug(meas_raw)
                measure = float(meas_raw)
                if measure > 500 or measure is None: # Arbitrary value
                    continue
                
                return measure
            except ValueError:
                # Try again
                pass
        
        
