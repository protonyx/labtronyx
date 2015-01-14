import models

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
            self._identity = resp.strip().split(',')
            
        except:
            self.logger.exception("Internal error while attaching to VISA instrument")
    
    def _onUnload(self):
        pass
    
    def getProperties(self):
        ret = models.m_Base.getProperties(self)
        
        ret['deviceVendor'] = 'Agilent'
            
        return ret
    
    def getMeasurement(self):
        # Attempt three times to get a measurement
        for x in range(3):
            try:
                meas_raw = self.__instr.ask(":FETCH?")
                measure = float(meas_raw)
                
                return measure
            except ValueError:
                # Try again
                pass
        