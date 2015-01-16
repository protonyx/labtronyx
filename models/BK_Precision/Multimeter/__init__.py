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
        # Clean up the SCPI header
        ind = resp.find(command) + len(command)
        if ind != -1:
            resp = resp[ind:]
            
        return resp
    
    def reset(self):
        self.__instr.write("*RST")

    def getFunction(self):
        return self._BK_ask(":FUNC?")

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
        cmd = ":" + self.func + ":RANG?"
        range_raw = self._BK_ask(cmd)
        self.logger.debug("Range: %s" % str(range_raw))

    def setRange(self, new_range):
        # :CURR:DC:RANG 20
        current_range = self.getRange()
        
        cmd = ":" + self.func + ":RANG"
        cmd1 = cmd + ":AUTO 0"
        cmd2 = cmd + " " + str(new_range)
        self.logger.debug(cmd1)
        self.__instr.write(cmd1)
        time.sleep(0.1)
        self.logger.debug(cmd2)
        self.__instr.write(cmd2)
        
    def getMeasurement(self):
        # Attempt three times to get a measurement
        for x in range(3):
            try:
                meas_raw = self._BK_ask(":FETCH?")
                self.logger.debug(meas_raw)
                measure = float(meas_raw)
                if measure > 500 or measure is None: # Arbitrary value
                    continue
                
                return measure
            except ValueError:
                # Try again
                pass
        
        
