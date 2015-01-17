import models
import time

class m_MultimeterBase(models.m_Base):
    
    # Model device type
    deviceType = 'Multimeter'
    
    # List of valid Controllers that are compatible with this Model
    validControllers = ['c_VISA', 'c_Serial']
    
    def _onLoad(self):
        self._identity = None
        self.controller = self.getControllerObject()
        
        try:
            # Use c_VISA
            self.__instr = self.controller.openResourceObject(self.resID)
            
            resp = self.__instr.ask("*IDN?")
            self._identity = resp.strip().split(',')

            self.func = self.getFunction
            
        except:
            self.logger.exception("Internal error while attaching to VISA instrument")
    
    def _onUnload(self):
        pass
    
    def getProperties(self):
        ret = models.m_Base.getProperties(self)
        
        ret['deviceVendor'] = 'BK Precision'
            
        return ret
    
    def _BK_ask(self, command):
        resp = str(self.__instr.ask(command))
        self.logger.debug(resp)
        
        # Check that the SCPI header was not retuned
        ind = resp.find(command)
        if ind != -1:
            ind = ind + len(command)
            resp = resp[ind:]
            
        return resp
    
    def reset(self):
        self.__instr.write("*RST")
        
    def getError(self):
        resp = self._BK_ask(":SYST:ERR?")
        return resp

    def getFunction(self):
        return self._BK_ask("FUNC?")

    def setFunction(self, func):
        self.func = func
        self.__instr.write(":FUNC %s" % self.func)
    
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
        self.__instr.write(cmd)
        
    def setRange_Auto(self):
        cmd = self.func + ":RANG:AUTO ON"
        self.logger.debug(cmd)
        self.__instr.write(cmd)

    def setRange(self, new_range):
        cmd = self.func + ":RANG " + str(new_range)
        
        self.logger.debug(cmd)
        self.__instr.write(cmd)
        
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
        
        
