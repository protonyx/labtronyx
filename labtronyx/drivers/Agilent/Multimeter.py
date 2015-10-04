"""
.. codeauthor:: Kevin Kennedy <protonyx@users.noreply.github.com>


"""
from labtronyx.bases import Base_Driver
from labtronyx.common.errors import *

import time
import re

info = {
    # Plugin author
    'author':               'KKENNEDY',
    # Plugin version
    'version':              '1.0',
    # Last Revision Date
    'date':                 '2015-10-04',
}

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
        'validResourceTypes':   ['VISA']
    }

    @classmethod
    def VISA_validResource(cls, identity):
        vendors = ['AGILENT TECHNOLOGIES', 'Agilent Technologies']
        return identity[0] in vendors and identity[1] in cls.info['deviceModel']
    
    modes = {
        'Capacitance': 'CAP',
        'Continuity': 'CONT',
        'AC Current': 'CURR:AC',
        'DC Current': 'CURR',
        'Diode': 'DIOD',
        'Frequency': 'FREQ',
        'Resistance': 'RES',
        '4-wire Resistance': 'FRES',
        'Period': 'PER',
        'Temperature': 'TEMP',
        'AC Voltage': 'VOLT:AC',
        'DC Voltage': 'VOLT'}
    
    trigger_sources = {
        'Continual': 'IMM',
        'Bus': 'BUS', 
        'External': 'EXT'
    }
    
    errors = {
        0: "No error",
        # Execution Errors
        -102: "Syntax error",
        -103: "Invalid separator",
        -113: "Undefined header",
        -123: "Numeric overflow",
        -151: "Invalid string data",
        -213: "INIT ignored",
        -222: "Data out of range; value not accepted",
        -222: "Data out of range; value clipped to upper limit",
        -222: "Data out of range; value clipped to lower limit",
        -222: "Data out of range; value clipped to lower limit",
        -224: "Illegal parameter value: ranges must be positive",
        -230: "Data stale",
        -231: "Internal software error",
        -292: "Referenced name does not exist",
        -330: "Self-test failed",
        -313: "Calibration memory lost; memory corruption detected",
        -313: "Calibration memory lost; due to firmware revision change",
        -314: "Save/recall memory lost; memory corruption detected",
        -314: "Save/recall memory lost; due to firmware revision change",
        -315: "Configuration memory lost; memory corruption detected",
        -315: "Configuration memory lost; due to firmware revision change",
        -330: "Self-test failed",
        -350: "Error queue overflow",
        -410: "Query INTERRUPTED",
        -420: "Query UNTERMINATED",
        # Instrument Errors
        201: "Memory lost: stored state",
        202: "Memory lost: power-on state",
        203: "Memory lost: stored readings",
        221: "Settings conflict: calculate limit state forced off",
        223: "Settings conflict: trig source changed to IMM",
        251: "Unsupported temperature transducer type",
        263: "Not able to execute while instrument is measuring",
        291: "Not able to recall state: it is empty",
        305: "Not able to perform requested operation",
        311: "Not able to specify resolution with Auto range",
        514: "Not allowed",
        521: "Communications: input buffer overflow",
        522: "Communications: output buffer overflow",
        532: "Not able to achieve requested resolution",
        540: "Cannot use overload as math reference",
        550: "Not able to execute command in local mode",
        624: "Unable to sense line frequency"}
    
    def open(self):
        self.getFunction()

    def close(self):
        self.enableFrontPanel()
        
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

    def trigger(self):
        """
        Used in conjunction with the Trigger Source to trigger the instrument from the remote interface. After setting
        the trigger source, you must place the multimeter in the "wait-for-trigger" state by calling
        :func:`waitForTrigger`.
        """
        self.write("*TRG")

    def waitForTrigger(self):
        """
        Change the state of the triggering system from "idle" to "wait-for-trigger". Measurements will begin when the
        specified trigger conditions are satisfied. Will also clear the previous set of readings from memory.
        """
        self.write("INIT")

        self.checkForError()

    def self_test(self):
        """
        Run the self-test suite

        +========+================================+
        | Test # | Test Name                      |
        +========+================================+
        | 600    | Front Panel Communications     |
        | 601    | Front Panel All On Test        |
        | 602    | A/D Feedback Test              |
        | 603    | Fine A/D Test                  |
        | 604    | Fine A/D Linearity             |
        | 605    | A/D & FE Measure Zero          |
        | 606    | Input Amplifier x100 Zero Test |
        | 607    | Input Amplifier x10 Zero Test  |
        | 608    | Input Amplifier x1 Zero Test   |
        | 609    | Input Leakage Test             |
        | 610    | Input Amplifier x10 Gain Test  |
        | 611    | Input Amplifier x1 Gain Test   |
        | 612    | Ohms 500nA Current Source      |
        | 613    | DC High Voltage Divider Test   |
        | 614    | Ohms 5uA Current Source Test   |
        | 615    | Ohms 10uA Current Source       |
        | 616    | Ohms 100uA to 200 Ohm Shunt    |
        | 617    | Ohms 1mA to 2 Ohm Shunt        |
        | 618    | High Current Shunt Test        |
        | 619    | AC 0.1VAC Zero Test            |
        | 620    | Precharge Amplifier Gain Test  |
        | 621    | Precharge Offset Range Test    |
        | 622    | FPGA Ping Test                 |
        +--------+--------------------------------+
        :return:
        """
        self.write("*TST?")

        self.checkForError()

    def checkForError(self):
        """
        Query the device for errors. Raises an exception if an error was registered on the device
        """
        errors = self.getErrors()

        if len(errors) == 1:
            code, msg = errors[0]
            raise DeviceError(msg)
        elif len(errors) > 1:
            raise DeviceError("Multiple errors")

    def _getError(self):
        # Get a single error
        ret = self.query("SYST:ERR?")
        code, msg = ret.split(',')
        code = int(code)
        msg = str(msg).strip()[1:-1]
        return (code, msg)
        
    def getErrors(self):
        """
        Get the last error
        
        :returns: tuple (code, msg)
        """
        errors = []

        code, msg = self._getError()
        while code != 0:
            errors.append((code, msg))
            code, msg = self._getError()

        return errors

    def enableFrontPanel(self):
        """
        Enables the front panel display if it was previously disabled.
        """
        self.write("DISP 1")
        self.write("DISP:WIND1:TEXT:CLEAR")
        self.write("DISP:WIND2:TEXT:CLEAR")

    def disableFrontPanel(self):
        """
        Disables the front panel display. Display can be re-enabled by calling
        `enableFrontPanel` or pressing the `LOCAL` button on the instrument.

        .. note:

           When the front panel is disabled, the instrument runs faster

        """
        self.write("DISP 0")

    def frontPanelText(self, text_top, text_bottom):
        """
        Set the text on the front panel of the instrument. The top line is limited to 12 characters, the bottom line to
        18 characters. You can use letters (A-Z), numbers (0-9), and special characters like "@", "%", "*", etc.
        Use "#" character to display a degree symbol.

        :param text_top: Top text (up to 12 characters)
        :type text_top: str
        :param text_bottom: Bottom text (up to 18 characters)
        :type text_bottom: str
        """
        if len(text_top) > 12:
            text_top = text_top[0:12]
        if len(text_bottom) > 18:
            text_bottom = text_bottom[0:18]

        if len(text_top) > 0:
            self.write('DISP:WIND1:TEXT "%s"' % text_top)
        if len(text_bottom) > 0:
            self.write('DISP:WIND2:TEXT "%s"' % text_bottom)

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
        mode = self.query("CONF?")

        mode = re.search(r'"([A-Z:]+)\s?([A-Z0-9,+\-.]*)"', mode)

        self.mode = mode.group(1)
        
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
                data = str(self.query("FETC?"))
                if ',' in data:
                    data = data.split(',')
                    return map(float, data)
                else:
                    return float(data)

            except ValueError:
                # Try again
                pass

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
        if source in self.trigger_sources.values():
            self.write("TRIG:SOUR %s" % source)
        else:
            raise ValueError('Invalid trigger source')

    def setSampleCount(self, samples):
        """
        Set the number of readings (samples) the multimeter will take per trigger.

        When the sample source is `Immediate`, the trigger delay value is used to determine how far apart the samples
        are to be taken. In `Timer` mode, the sample timer value is used.

        :param samples: Number of samples
        :type samples: int
        """
        self.write("SAMP:COUN %s" % samples)

        self.checkForError()

    def getSampleCount(self):
        """
        Get the number of readings (samples) the multimeter will take per trigger.

        :return: Number of samples (int)
        """
        return int(self.query("SAMP:COUN?"))