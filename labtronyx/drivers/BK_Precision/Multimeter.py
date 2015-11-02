"""
.. codeauthor:: Kevin Kennedy <protonyx@users.noreply.github.com>

Driver
------

The BK Precision Multimeters use a Silicon Labs `CP210x USB to UART Bridge`. This
requires a third party driver that must be downloaded from the BK Precision
website before connecting the device.

That driver can be downloaded from
`here <https://bkpmedia.s3.amazonaws.com/downloads/software/Bench_Multimeter_USB_Drivers.zip>`_

The driver officially supports Windows XP, Vista, 7

Configuration
-------------

In order to be recognized by the VISA driver, the instrument must be configured
with a baudrate of `9600`. This must be done on the instrument following the
directions given in the
`user's guide <https://bkpmedia.s3.amazonaws.com/downloads/manuals/en-us/2831Eand5491B_manual.pdf>`_
"""
from labtronyx.bases import DriverBase
from labtronyx.common.errors import *


class d_2831(DriverBase):
    """
    Driver for BK Precision 2831E and 5491B Digital Multimeters
    """
    author = 'KKENNEDY'
    version = '1.0'
    deviceType = 'Multimeter'
    compatibleInterfaces = ['VISA']
    compatibleInstruments = {
        'BK Precision': ['2831E', '5491B', '5492B', '5492BGPIB']
    }

    @classmethod
    def VISA_validResource(cls, identity):
        models = ['2831E  Multimeter', '5491B Digital Multimeter']
        return identity[0] in models
    
    modes = {
        'AC Voltage': 'VOLT:AC',
        'DC Voltage': 'VOLT:DC',
        'Resistance': 'RES',
        '4-wire Resistance': 'FRES',
        'AC Current': 'CURR:AC',
        'DC Current': 'CURR:DC',
        'Frequency': 'FREQ',
        'Period': 'PER',
        'Diode': 'DIOD',
        'Continuity': 'CONT' }
    
    trigger_sources = {
        'Continual': 'IMM', 
        'Bus': 'BUS', 
        'External': 'MAN'}
    
    def open(self):
        self.func = self.getFunction()
    
    def close(self):
        pass
        
    def getProperties(self):
        return {
            # Override VISA defaults, this device is different
            'deviceVendor':        'BK Precision',
            'deviceModel':         self.getIdentity()[0].split(' ')[0],

            'validModes':          self.modes,
            'validTriggerSources': self.trigger_sources
        }
    
    def query(self, command):
        resp = str(self.query(command))
        resp = resp.strip() # Strip whitespace
        
        # Check that the SCPI header was not retuned
        ind = resp.find(command)
        if ind != -1:
            ind = ind + len(command)
            resp = resp[ind:]
            
        return resp
    
    def reset(self):
        """
        Reset the instrument
        """
        self.write("*RST")
        
    def getError(self):
        """
        Gets the last error message from the device.
        
        :returns: str
        """
        return self.query(":SYS:ERR?")
        
    def enableFrontPanel(self):
        """
        Enables the front panel display if it was previously disabled.
        """
        self.write(":DISP:ENAB 1")
        
    def disableFrontPanel(self):
        """
        Disables the front panel display. Display can be re-enabled by calling
        `enableFrontPanel` or pressing the `LOCAL` button on the instrument.
        
        .. note:
        
           When the front panel is disabled, the instrument runs faster
        
        """
        self.write(":DISP:ENAB 0")

    def setMode(self, func):
        """
        Set the configuration mode
        
        Valid modes:
         
          * 'AC Voltage'
          * 'DC Voltage'
          * 'Resistance'
          * 'AC Current'
          * 'DC Current'
          * 'Frequency'
          * 'Period'
          * 'Diode'
          * 'Continuity'
          
        :param func: Configuration mode
        :type func: str
        """
        if func in self.modes:
            value = self.modes.get(func)
            self.write(":FUNC %s" % str(value))
            self.func = value
        else:
            raise RuntimeError("Invalid Function")
        
    def getMode(self):
        """
        Get the current operating mode
        
        :returns: str
        """
        self.mode = str(self.query("FUNC?")).upper()
        
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
    
    def setRange(self, value):
        """
        Set the range for the measurement. The range is selected by specifying
        the expected reading as an absolute value. The instrument will then
        go to the most ideal range that will accomodate the expected reading
        
        Possible values for `value`:
        
           * 'MIN' or '0'
           * Number (see ranges below)
           * 'DEFAULT'
           * 'MAX'
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
        if self.func.upper() in ['FREQ', 'PER']:
            self.write(":%s:THR:VOLT:RANG %s" % (self.func, value))
        else:
            if value in ['auto', 'AUTO']:
                self.write(":%s:RANG:AUTO ON" % self.func)
            else:
                self.write(":%s:RANG:AUTO OFF" % self.func)
                self.write(":%s:RANG %s" % (self.func, str(value)))

    def getRange(self):
        """
        Get the range for the measurement.
        
        :returns: float
        """
        return float(self.query(self.func + ":RANG?"))
    
    def setIntegrationRate(self, value):
        """
        Set the integration period (measurement speed) for the basic measurement
        functions (except frequency and period). Expressed as a factor of the 
        power line frequency.
        
        .. note:
           
           A rate of 1 would result in 16.67 ms integration period (Assuming
           60 hz power line frequency.
           
        :param value: Integration rate
        :type value: 
        """
        self.write(":%s:NPLC %s" % (self.func, str(value)))
    
    def getIntegrationRate(self):
        """
        Get the integration period (measurement speed). Expressed as a factor
        of the power line frequency.
        
        :returns: float
        """
        return float(self.query(":%s:NPLC?" % (self.func)))
    
    def setMeasurementOffset(self, value=None):
        """
        Establish a reference value for the measurement. When the offset is
        set, the result of a measurement will be the algebraic difference
        between the reference value and the current reading.
        
        Expected value ranges:
        
           * DC Voltage: 0 to 1000 Volts
           * AC Voltage: 0 to 750 Volts
           * Current: 0 to 20 Amps
           * Resistance: 0 to 20e6 ohms
           
        :param value: Reference value
        :type value: float
        """
        if value is None:
            self.write(":%s:REF:ACQ" % self.func)
        elif float(value) == 0.0:
            self.write(":%s:REF:STATE OFF" % self.func)
        else:
            self.write(":%s:REF %s" % (self.func, str(value)))
            
    def getMeasurementOffset(self):
        """
        Get the current measurement offset value.
        
        :returns: float
        """
        return float(self.query(":%s:REF?" % self.func))
    
    def zeroMeasurement(self):
        """
        Reads the current measurement and set it as the offset.
        """
        self.setMeasurementOffset()
        
    def setTriggerSource(self, value):
        """
        Set the trigger source for a measurement.
        
        Valid values:
        
          * `Continual`: Internal continuous trigger
          * `Bus`: Triggered via USB/RS-232 Interface
          * `External`: Triggered via the `Trig` button on the front panel
          
        :param value: Trigger source
        :type value: str
        """
        
        if value in self.trigger_sources:
            self.write(":TRIG:SOUR %s" % self.trigger_sources.get(value))
        else:
            raise ValueError('Invalid trigger source')
    
    def getTriggerSource(self):
        """
        Get the trigger source for a measurement.
        
        :returns: str
        """
        trig = str(self.query("TRIG:SOUR?")).upper()
        
        for key, value in self.trigger_sources.items():
            if trig == value:
                return key
            
        return 'Unknown'
    
    def trigger(self):
        """
        Triggers the measurement if trigger source is set to `Bus`
        """
        self.write("*TRG")
        
    def getMeasurement(self):
        """
        Get the last available reading from the instrument. This command does
        not trigger a measurement if trigger source is not set to `IMMEDIATE`.
        
        :returns: float
        """
        # Attempt three times to get a measurement
        for x in range(3):
            try:
                return float(self.query("FETC?"))
            except ValueError:
                # Try again
                pass
        
        
