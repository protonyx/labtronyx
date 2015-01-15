import models

import time

class m_3441XA(models.m_Base):
    
    # Model device type
    deviceType = 'Multimeter'
    
    # List of valid Controllers that are compatible with this Model
    validControllers = ['c_VISA']
    
    validVIDs = ['Agilent']
    validPIDs = ['34410A', '34411A', 'L4411A']
    
    modes = {
        'Capacitance': 'CAP',
        'Continuity': 'CONT',
        'AC Current': 'CURR:AC',
        'DC Current': 'CURR:DC',
        'Diode': 'DIOD',
        'Frequency': 'FREQ',
        '4-wire Resistance': 'FRES',
        'Temperature': 'TEMP',
        'AC Voltage': 'VOLT:AC',
        'DC Voltage': 'VOLT:DC'}
    
    def _onLoad(self):
        self._identity = None
        self.controller = self.getControllerObject()
        
        try:
            # Use c_VISA
            self.__instr = self.controller.openResourceObject(self.resID)
            
            resp = self.__instr.ask("*IDN?")
            self.__identity = resp.strip().split(',')
            
        except:
            self.logger.exception("Internal error while attaching to VISA instrument")
    
    def _onUnload(self):
        pass
    
    def getProperties(self):
        ret = models.m_Base.getProperties(self)
        
        ret['deviceVendor'] = 'Agilent'
        
        if self.__identity is not None:
            ret['deviceModel'] = self.__identity[1]
            
        return ret
    
    def reset(self):
        self.__instr.write("*RST")

    def getFunction(self):
        return self.__instr.ask("CONF?")

    def setFunction(self, func):
        self.func = func
        self.__instr.write("CONF:%s" % self.func)
    
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

    def setRange(self, new_range):
        # Set to autorange no matter what is passed
        self.__instr.write('SENS:VOLT:DC:RANGE:AUTO ON')
    
    def getMeasurement(self):
        # Attempt three times to get a measurement
        for x in range(3):
            try:
                # Initiate a measurement
                self.__instr.write("INIT")
                time.sleep(0.1)
                
                meas_raw = self.__instr.ask("FETC?")
                measure = float(meas_raw)
                
                return measure
            except ValueError:
                # Try again
                pass
        