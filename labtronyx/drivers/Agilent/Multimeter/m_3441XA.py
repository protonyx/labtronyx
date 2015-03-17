from Base_Driver import Base_Driver

import time

class m_3441XA(Base_Driver):
    
    info = {
        # Model revision author
        'author':               'KKENNEDY',
        # Model version
        'version':              '1.0',
        # Revision date of Model version
        'date':                 '2015-01-31',
        # Device Manufacturer
        'deviceVendor':         'Agilent',
        # List of compatible device models
        'deviceModel':          ['34410A', '34411A', 'L4411A'],
        # Device type    
        'deviceType':           'Multimeter',      
        
        # List of compatible resource types
        'validResourceTypes':   ['VISA'],  
        
        #=======================================================================
        # VISA Attributes        
        #=======================================================================
        # Compatible VISA Manufacturers
        'VISA_compatibleManufacturers': ['AGILENT TECHNOLOGIES',
                                         'Agilent Technologies'],
        # Compatible VISA Models
        'VISA_compatibleModels':        ['34410A', '34411A', 'L4411A']
    }
    
    modes = {
        'Capacitance': 'CAP',
        'Continuity': 'CONT',
        'AC Current': 'CURR:AC',
        'DC Current': 'CURR:DC',
        'Diode': 'DIOD',
        'Frequency': 'FREQ',
        'Resistance': 'RES',
        '4-wire Resistance': 'FRES',
        'Period': 'PER',
        'Temperature': 'TEMP',
        'AC Voltage': 'VOLT:AC',
        'DC Voltage': 'VOLT:DC'}
    
    def _onLoad(self):
        self.instr = self.getResource()
        self.instr.open()
    
    def _onUnload(self):
        pass
    
    def reset(self):
        self.instr.write("*RST")

    def getFunction(self):
        return self.instr.query("CONF?")

    def setFunction(self, func):
        self.func = func
        self.instr.write("CONF:%s" % self.func)
    
    def setFunction_DC_Voltage(self):
        self.setFunction("VOLT:DC")
        
    def setFunction_AC_Voltage(self):
        self.setFunction("VOLT:AC")
        
    def setFunction_DC_Current(self):
        self.setFunction("CURR:DC")
        
    def setFunction_AC_Current(self):
        self.setFunction("CURR:AC")
        
    def setFunction_Resistance(self, mode):
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
        self.instr.write('SENS:VOLT:DC:RANGE:AUTO ON')
    
    def getMeasurement(self):
        # Attempt three times to get a measurement
        for x in range(3):
            try:
                # Initiate a measurement
                self.instr.write("INIT")
                time.sleep(0.1)
                
                meas_raw = self.instr.query("FETC?")
                measure = float(meas_raw)
                
                return measure
            except ValueError:
                # Try again
                pass
        
    def getQuickMeasurement(self, mode):
        # Quick Capacitance Measurement
        possiblemodes = ['CAP', 'CONT', 'CURR', 'DIOD', 'FREQ', 'FRES', 'PER', 'RES', 'TEMP', 'VOLT:AC', 'VOLT:DC']

        if mode in possiblemodes:
            return self.instr.query("MEAS:%s?" % mode)
        else:
            raise ValueError

    def set_Aperture(self, mode, time):
        # Set the aperture for different modes
        possiblemodes = ['CURR', 'FREQ', 'FRES', 'PER', 'RES', 'TEMP', 'VOLT']

        if mode in possiblemodes:
            self.instr.write("%s:APER %s" % (mode,time))
        else:
            raise ValueError

    def showError(self):
        return self.instr.query("SYST:ERR?")

    def CalculateMath(self, function):
        possibleMath = ['NULL', 'DB', 'DBM', 'AVER', 'LIM']

        if function in possibleMath:
            return self.instr.query("CALC:FUNC %s" % function)
        else:
            raise ValueError

    def Trigger(self, Trig):
        possibleTrig = ['COUN', 'DEL', 'LEV', 'SLOP', 'SOUR']

        if Trig in possibleTrig:
            return self.instr.write("TRIG:%s" % Trig)
