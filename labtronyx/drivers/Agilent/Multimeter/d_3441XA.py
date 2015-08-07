"""
.. codeauthor:: Kevin Kennedy <protonyx@users.noreply.github.com>


"""
from labtronyx.bases import Base_Driver, DeviceError

import time

class d_3441XA(Base_Driver):
    """
    Driver for Agilent 34410A and 34411A Digital Multimeter
    """
    
    info = {
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
    
    trigger_sources = {
        'Continual': 'IMMEDIATE',
        'Bus': 'BUS', 
        'External': 'EXTERNAL'
    }
    
    errors = {
        -102: "Syntax error",
        -420: "Query UNTERMINATED"}
    
    def open(self):
        self.getFunction()

    def close(self):
        pass
        
    def getProperties(self):
        return dict(
            validModes=self.modes,
            validTriggerSources=self.trigger_sources
        )
    
    def reset(self):
        """
        Reset the instrument
        """
        self.write("*RST")
        
    def checkForError(self):
        """
        Raise an exception if an error was registered on the device
        """
        errors = []
        code = -1
        
        while (code != 0):
            code, msg = self.getError()
            
            if code != 0:
                errors.append(code)
        
        if len(errors) > 0:
            raise DeviceError(self.errors.get(errors[0], 'Unknown Error'))
        
    def getError(self):
        """
        Get the last error
        
        :returns: tuple (code, msg)
        """
        ret = self.query("SYST:ERR?")
        code, msg = ret.split(',')
        code = int(code)
        msg = str(msg).strip()[1:-1]
        return (code, msg)

    def setMode(self, func):
        """
        Set the configuration mode
        
        Valid modes:
         
           * 'AC Voltage'
           * 'DC Voltage'
           * 'Resistance'
           * '4-wire Resistance'
           * 'AC Current'
           * 'DC Current'
           * 'Frequency'
           * 'Period'
           * 'Diode'
           * 'Continuity'
           * 'Capacitance
           * 'Temperature'
          
        :param func: Configuration mode
        :type func: str
        """
        if func in self.modes:
            value = self.modes.get(func)
            self.write("CONF:%s" % value)
        else:
            raise ValueError("Invalid Function")
    
    def getMode(self):
        """
        Get the current operating mode
        
        :returns: str
        """
        self.mode = str(self.query("CONF?")).upper()
        
        for desc, code in self.modes.items():
            if self.mode == code:
                self.func = code
                return desc
            
        return 'Unknown'
    
    def setFunction(self, value):
        """
        Alias for `setMode`
        """
        return self.setMode(value)
    
    def getFunction(self):
        """
        Alias for `getMode`
        """
        return self.getMode()
    
    def getRange(self):
        """
        Get the range for the measurement.
        
        :returns: float
        """
        return self.query("SENS:%s:RANGE?" % self.func)
    
    def setRange(self, new_range):
        """
        Set the range for the measurement. The range is selected by specifying
        the expected reading as an absolute value. The instrument will then
        go to the most ideal range that will accomodate the expected reading
        
        Possible values for `value`:
        
           * 'AUTO'
           
        Expected value ranges:
        
           * DC Voltage: 0 to 1000 Volts
           * AC Voltage: 0 to 750 Volts
           * Current: 0 to 20 Amps
           * Resistance: 0 to 20e6 ohms
           * Frequency or Period: 0 to 1010 Volts
        
        :param value: Measurement Range
        :type value: str
        """
        if str(new_range).upper() == 'AUTO':
            self.write('SENS:%s:RANGE:AUTO ON' % self.func)
        else:
            self.write('SENS:%s:RANGE:AUTO OFF' % self.func)
            
    def getMeasurement(self):
        """
        Get the last available reading from the instrument. This command does
        not trigger a measurement if trigger source is not set to `IMMEDIATE`.
        
        :returns: float
        """
        # Attempt three times to get a measurement
        for x in range(3):
            try:
                # Initiate a measurement
                self.write("INIT")
                time.sleep(0.01)
                return float(self.query("FETC?"))
            except ValueError:
                # Try again
                pass
        
    def getQuickMeasurement(self, mode):
        """
        Get a quick measurement using the default mode configuration
        
        :param mode: Operating mode
        :type mode: str
        :returns: float
        """
        if mode in self.modes:
            val = self.modes.get(mode)
            return float(self.query("MEAS:%s?" % val))
        else:
            raise ValueError('Invalid Mode')

    def setIntegrationRate(self, value):
        """
        Set the integration period (measurement speed) for the basic measurement
        functions (except frequency and period). Expressed as a factor of the 
        power line frequency (PLC = Power Line Cycles).
        
        Valid values: 0.006, 0.02, 0.06, 0.2, 1, 2, 10, 100
        
        Value of 'DEF' sets the integration rate to 1 PLC
        
        .. note:
           
           A rate of 1 would result in 16.67 ms integration period (Assuming
           60 hz power line frequency.
           
        :param value: Integration rate
        :type value: 
        """
        self.write("SENS:%s:NPLC %s" % (self.func, str(value)))
    
    def getIntegrationRate(self):
        """
        Get the integration period (measurement speed). Expressed as a factor
        of the power line frequency.
        
        :returns: float
        """
        return float(self.query(":%s:NPLC?" % (self.func)))
        
    def setTriggerCount(self, count):
        """
        This command selects the number of triggers that will be accepted by 
        the meter before returning to the "idle" trigger state.
        
        A value of '0' will set the multimeter into continuous trigger mode.
        
        :param count: Number of triggers
        :type count: int
        """
        self.write("TRIG:COUN %i" % int(count))
        
    def setTriggerDelay(self, delay=None):
        """
        This command sets the delay between the trigger signal and the first 
        measurement. This may be useful in applications where you want to allow 
        the input to settle before taking a reading or for pacing a burst of 
        readings. The programmed trigger delay overrides the default trigger 
        delay that the instrument automatically adds.
        
        If delay is not provided, the automatic trigger delay is enabled
        
        Note::
        
           The Continuity and Diode test functions ignore the trigger delay
           setting
        
        :param delay: Trigger delay (in seconds)
        :type delay: float
        """
        if delay is None:
            self.write("TRIG:DEL:AUTO ON")
        else:
            self.write("TRIG:DEL:AUTO OFF")
            self.write("TRIG:DEL %f" % float(delay))

    def setTriggerSource(self, source):
        """
        Set the trigger source for a measurement.
        
        Valid values:
        
          * `IMMEDIATE`: Internal continuous trigger
          * `BUS`: Triggered via USB/RS-232 Interface
          * `EXTERNAL`: Triggered via the 'Ext Trig Input' BNC connector
          
        For the EXTernal source, the instrument will accept a hardware trigger 
        applied to the rear-panel Ext Trig Input BNC connector. The instrument 
        takes one reading, or the specified number of readings (sample count), 
        each time a TTL pulse (low-true for slope = negative) is received. If 
        the instrument receives an external trigger before it is ready to accept 
        one, it will buffer one trigger.
          
        :param source: Trigger source
        :type source: str
        """
        validSources = ['IMMEDIATE', 'BUS', 'EXTERNAL']
        
        if source in validSources:
            self.write("TRIG:SOUR %s" % source)
        else:
            raise ValueError('Invalid trigger source')

