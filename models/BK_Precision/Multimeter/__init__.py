import models

class m_MultimeterBase(models.m_Base):
    
    # Model device type
    deviceType = 'Multimeter'
    
    # List of valid Controllers that are compatible with this Model
    validControllers = ['c_VISA', 'c_Serial']
    
    def _onLoad(self):
        self._identity = None
        
        try:
            # Use c_VISA
            self.__instr = self.controller._getInstrument(self.resID)
            
            resp = self.__instr.ask("*IDN?")
            self._identity = resp.strip().split(',')
            
        except:
            self.logger.exception("Internal error while attaching to VISA instrument")
    
    def _onUnload(self):
        pass
    
    def reset(self):
        self.__instr.write("*RST")
    
    def setFunction_DC_Voltage(self):
        self.__instr.write(":FUNC VOLT:DC")
        
    def setFunction_AC_Voltage(self):
        self.__instr.write(":FUNC VOLT:AC")
        
    def setFunction_DC_Current(self):
        self.__instr.write(":FUNC CURR:DC")
        
    def setFunction_AC_Current(self):
        self.__instr.write(":FUNC CURR:AC")
        
    def setFunction_Resistance(self):
        self.__instr.write(":FUNC RES")
        
    def setFunction_Frequency(self):
        self.__instr.write(":FUNC FREQ")
        
    def setFunction_Period(self):
        self.__instr.write(":FUNC PER")
        
    def setFunction_Diode(self):
        self.__instr.write(":FUNC DIOD")
        
    def setFunction_Continuity(self):
        self.__instr.write(":FUNC CONT")
        
    def getMeasurement(self):
        measure = self.__instr.ask(":FETCH?")
        
        #:FUNC VOLT:DC
        #:FETCH?
        #-8.98e-5
        
        pass
        
        