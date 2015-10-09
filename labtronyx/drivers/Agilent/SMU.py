"""
.. codeauthor:: Kevin Kennedy <protonyx@users.noreply.github.com>

"""
from labtronyx.bases import Base_Driver
from labtronyx.common.errors import *

info = {
    # Plugin author
    'author':               'KKENNEDY',
    # Plugin version
    'version':              '1.0',
    # Last Revision Date
    'date':                 '2015-10-04',
}

class d_B29XX(Base_Driver):
    """
    Driver for Agilent B2901A and B2902A Source Measurement Units
    """
    
    info = {
        # Device Manufacturer
        'deviceVendor':         'Agilent',
        # List of compatible device models
        'deviceModel':          ['B2901A', 'B2902A'],
        # Device type    
        'deviceType':           'Source Measurement Unit',      
        
        # List of compatible resource types
        'validResourceTypes':   ['VISA']
    }

    @classmethod
    def VISA_validResource(cls, identity):
        return identity[0].upper() == 'AGILENT TECHNOLOGIES' and identity[1] in cls.info['deviceModel']

    VALID_MODES = {
        'Voltage':       'VOLT',
        'Current':       'CURR',
        'Resistance':    'RES'
    }

    VALID_SOURCE_MODES = {
        'Sweep': 'SWEEP',
        'Fixed': 'FIXED',
        'List':  'LIST'
    }

    VALID_TRIGGER_SOURCES = ['AINT', 'BUS', 'TIMER', 'INT1', 'INT2', 'LAN', 'EXT1', 'EXT2',
                    'EXT3', 'EXT4', 'EXT5', 'EXT6', 'EXT7', 'EXT8', 'EXT9', 'EXT10',
                    'EXT11', 'EXT12', 'EXT13', 'EXT14']

    # Instrument Constants
    MIN_APERTURE_TIME = 0.000008
    MAX_APERTURE_TIME = 2.0

    def open(self):
        prop = self.resource.getProperties()

        # Identify the number of channels available
        if prop.get('deviceModel') == 'B2901A':
            self.NUM_CHANNELS = 1
        elif prop.get('deviceModel') == 'B2902A':
            self.NUM_CHANNELS = 2
        else:
            self.NUM_CHANNELS = 1

        # Get the current device mode
        self._mode_source = {}
        self._mode_measure = {}
        for idx in range(1, self.NUM_CHANNELS + 1):
            self.getSourceMode(idx)
            self.getMeasureMode(idx)

    def close(self):
        pass

    def getProperties(self):
        return dict(
            validModes=self.VALID_MODES,
            validTriggerSources=self.VALID_TRIGGER_SOURCES
        )

    def getError(self):
        """
        Get the last recorded error from the instrument

        :return: error code, error message
        """
        err = self.query(':SYST:ERR?')
        return err.split(',')

    def getErrors(self):
        """
        Retrieve any queued errors on the instrument

        :return:                list
        """
        # TODO: Replace with ERR:ALL on the real device, this is just for sim
        errors = [] # self.query(':SYST:ERR:ALL?')

        while True:
            err_num, err_msg = self.getError()
            if float(err_num) == 0:
                break
            else:
                errors.append((err_num, err_msg,))

        return errors

    def enableFrontPanel(self):
        """
        Enables the front panel display if it was previously disabled.
        """
        self.write(":DISP:ENAB 1")
        self.write(":DISP:WIND1:TEXT:STAT 0")
        self.write(":DISP:WIND2:TEXT:STAT 0")

    def disableFrontPanel(self):
        """
        Disables the front panel display. Display can be re-enabled by calling
        `enableFrontPanel` or pressing the `LOCAL` button on the instrument.

        .. note:

           When the front panel is disabled, the instrument runs faster

        """
        self.write(":DISP:ENAB 0")

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
            self.write(":DISP:WIND1:TEXT:STAT 1")
            self.write(':DISP:WIND1:TEXT:DATA "%s"' % text_top)

        if len(text_bottom) > 0:
            self.write(":DISP:WIND2:TEXT:STAT 1")
            self.write(':DISP:WIND2:TEXT:DATA "%s"' % text_bottom)

    def setSourceMode(self, channel, output_mode='VOLT'):
        """
        Sets the instrument source mode.

        :param channel:         SMU Channel
        :type channel:          int
        :param output_mode:     Source output mode. Current ('CURR') or Voltage ('VOLT')
        :type output_mode:      str
        :raises:                RuntimeError on verification failure
        """
        validSource = {'VOLTAGE': 'VOLT',
                       'VOLTAGE:DC': 'VOLT',
                       'CURRENT': 'CURR',
                       'CURRENT:DC': 'CURR'}

        mode = validSource.get(output_mode.upper(), output_mode.upper())

        self.write(':SOUR{0}:FUNC:MODE {1}'.format(channel, mode))

        # Verify
        if self.getSourceMode(channel).upper() != mode.upper():
            raise RuntimeError('Set value failed verification')

    def getSourceMode(self, channel):
        """
        Get the instrument source mode. Returns 'VOLT' (Voltage) or 'CURR' (Current)

        :param channel:         SMU Channel
        :type channel:          int
        :return:                str
        """
        mode = self.query(':SOUR{0}:FUNC:MODE?'.format(channel))
        self._mode_source[channel] = mode

        return mode

    def setSourceVoltage(self, channel, voltage_base, voltage_trig=None):
        """
        Set the source output voltage. `voltage_trig` is used to specify a voltage level when the instrument is
        triggered

        :param channel:         SMU Channel
        :type channel:          int
        :param voltage_base:    Base voltage when power output is enabled
        :type voltage_base:     float
        :param voltage_trig:    Voltage when power output is enabled and instrument is triggered
        :type voltage_trig:     float
        :raises:                RuntimeError on verification failure
        """
        if voltage_trig is None:
            voltage_trig = voltage_base

        self.setSourceMode(channel, 'VOLT')

        self.write(':SOUR{0}:VOLT {1}'.format(channel, voltage_base))
        self.write(':SOUR{0}:VOLT:TRIG {1}'.format(channel, voltage_trig))

        # Verify
        if self.getSourceVoltage(channel) != voltage_base:
            raise RuntimeError('Set value failed verification')

    def getSourceVoltage(self, channel):
        """
        Get the source output voltage

        :param channel:         SMU Channel
        :type channel:          int
        :return:                float
        """
        return float(self.query(':SOUR{0}:VOLT?'.format(channel)))

    def setSourceCurrent(self, channel, current_base, current_trig=None):
        """
        Set the source output current. `current_trig` is used to specify a current level when the instrument is
        triggered

        :param channel:         SMU Channel
        :type channel:          int
        :param current_base:    Base current when power output is enabled
        :type current_base:     float
        :param current_trig:    Current when power output is enabled and instrument is triggered
        :type current_trig:     float
        :raises:                RuntimeError on verification failure
        """
        if current_trig is None:
            current_trig = current_base

        self.setSourceMode(channel, 'CURR')

        self.write(':SOUR{0}:CURR {1}'.format(channel, current_base))
        self.write(':SOUR{0}:CURR:TRIG {1}'.format(channel, current_trig))

        # Verify
        if self.getSourceCurrent(channel) != current_base:
            raise RuntimeError('Set value failed verification')

    def getSourceCurrent(self, channel):
        """
        Get the source output current

        :param channel:         SMU Channel
        :type channel:          int
        :return:                float
        """
        return float(self.query(':SOUR{0}:CURR?'.format(channel)))

    def setMeasureMode(self, channel, measure_mode):
        """
        Enable measurement functions. Instrument can measure Voltage ('VOLT'), Current ('CURR') or Resistance ('RES')

        :param channel:         SMU Channel
        :type channel:          int
        :param measure_mode:    Measurement function
        :type measure_mode:     str
        :raises:                RuntimeError on verification failure
        """
        validMeas = {
            'VOLTAGE':    'VOLT',
            'VOLTAGE:DC': 'VOLT',
            'CURRENT':    'CURR',
            'CURRENT:DC': 'CURR',
            'RESISTANCE': 'RES'
        }

        mode = validMeas.get(measure_mode.upper(), measure_mode.upper())

        self.write(':SENS{0}:FUNC {1}'.format(channel, mode))

        # Verify
        if self.getMeasureMode(channel).upper() != mode.upper():
            raise RuntimeError('Set value failed verification')

    def getMeasureMode(self, channel):
        """
        Get the enabled measurement functions

        :param channel:         SMU Channel
        :type channel:          int
        :return:                str
        """
        mode = self.query(':SENS{0}:FUNC:ON?'.format(channel))
        self._mode_measure[channel] = mode

        return mode

    def setApertureTime(self, channel, apertureTime):
        """
        Sets the integration time for one point measurement. Aperture time must be between 8e-6 to 2 seconds. If the
        value specified is less than MIN or greater than MAX, the value is automatically set to MIN or MAX.

        :param channel:         SMU Channel
        :type channel:          int
        :param apertureTime:    Aperture Integration time in seconds
        :type apertureTime:     float
        :raises:                RuntimeError on verification failure
        """
        if apertureTime < self.MIN_APERTURE_TIME or apertureTime > self.MAX_APERTURE_TIME:
            self.logger.warning("Aperture time should be between {0} and {1}".format(
                self.MIN_APERTURE_TIME, self.MAX_APERTURE_TIME)
            )

        mode = self._mode_measure.get(channel, 'VOLT')
        self.write(':SENS{0}:{1}:APER {2}'.format(channel, mode, apertureTime))

        # Verify
        if self.getApertureTime(channel) != apertureTime:
            raise RuntimeError('Set value failed verification')

    def getApertureTime(self, channel):
        """
        Get the instrument aperture time.

        :param channel:         SMU Channel
        :type channel:          int
        :return:                float
        """
        mode = self._mode_measure.get(channel, 'VOLT')
        return float(self.query(':SENS{0}:{1}:APER?'.format(channel, mode)))

    def enableAutoAperture(self, channel):
        """
        Enables the auto aperture function. When enabled, the instrument automatically sets the integration time
        suitable for the measurement range.

        :param channel:         SMU Channel
        :type channel:          int
        """
        mode = self._mode_measure.get(channel, 'VOLT')
        self.write(':SENS{0}:{1}:APER:AUTO 1'.format(channel, mode))

    def disableAutoAperture(self, channel):
        """
        Disables the auto aperture function.

        :param channel:         SMU Channel
        :type channel:          int
        """
        mode = self._mode_measure.get(channel, 'VOLT')
        self.write(':SENS{0}:{1}:APER:AUTO 0'.format(channel, mode))

    def enableRemoteSense(self, channel):
        pass

    def disableRemoteSense(self, channel):
        pass

    def setMeasurementRange(self, channel, range):
        pass

    def getMeasurementRange(self, channel):
        pass

    def setTraceBufferPoints(self, channel, data_points):
        """
        Sets the size of the instrument trace buffer. The maximum number of data points in the trace buffer is 100,000.

        :param channel:         SMU Channel
        :type channel:          int
        :param data_points:     Number of data points to record in the trace buffer
        :type data_points:      int
        """
        self.write(":TRAC{0}:POIN {1}".format(channel, data_points))
        # TODO: Should we verify this?

    def getTraceBufferPoints(self, channel):
        """
        Get the size of the instrument trace buffer, and the number of data points currently in the buffer

        :param channel:         SMU Channel
        :type channel:          int
        :return:                Buffer size, number of points in the buffer
        """
        buf_size = self.query(":TRAC{0}:POIN?".format(channel))
        buf_act = self.query(":TRAC{0}:POIN:ACT?".format(channel))

        return buf_size, buf_act

    def enableTraceBuffer(self, channel):
        """
        Enables the trace buffer to start collecting data points. Buffer size is set using `setTraceBufferPoints`.

        :param channel:         SMU Channel
        :type channel:          int
        """
        self.write(":FORM:ELEM:SENS VOLT,CURR,TIME")
        self.write(":TRAC{0}:FEED SENS".format(channel)) # Get data from the measurement unit
        self.write(":TRAC{0}:TST:FORM ABS".format(channel)) # Absolute timestamps

        # Enable the trace buffer
        self.write(":TRAC{0}:FEED:CONT NEXT".format(channel))

    def clearTraceBuffer(self, channel):
        """
        Clears the trace buffer of the specified channel.

        :param channel:         SMU Channel
        :type channel:          int
        """
        # Disable the trace buffer
        self.write(":TRAC{0}:FEED:CONT NEV".format(channel))

        # Clear the buffer
        self.write(":TRAC{0}:CLE".format(channel))

    def getTraceBuffer(self, channel, offset=0, size=None):
        """
        Returns data in the trace buffer of the specified channel.

        :param channel:         SMU Channel
        :type channel:          int
        :param offset:          Indicates the beginning index of the data
        :type offset:           int
        :param size:            Number of data bytes to retrieve
        :type size:             int
        :return:
        """
        # TODO: Validate
        return self.query(":TRAC{0}:DATA?".format(channel))

    def setTriggerSource(self, channel, triggerSource):
        pass

    def setTriggerCount(self, channel, number):
        """
        Set the trigger count for the specified device action

        :param channel:         SMU Channel
        :type channel:          int
        :param number:          Number of triggers
        :type number:           int
        :return:
        """
        self.write(":TRIG{0}:COUN {1}".format(channel, number))

    def setTriggerDelay(self, channel, delay):
        pass

    def setTriggerInterval(self, channel, interval):
        pass

    def setTriggerSetup(self, triggerSource, number, interval, delay=0):
        """
        Set SMU Trigger settings
        
        :param triggerSource: Trigger Source - ['AINT', 'BUS', 'TIMER', 'INT1', 'INT2', 'LAN', 'EXT1', 'EXT2',\
                    'EXT3', 'EXT4', 'EXT5', 'EXT6', 'EXT7', 'EXT8', 'EXT9', 'EXT10',\
                    'EXT11', 'EXT12', 'EXT13', 'EXT14']
        :type triggerSource: str
        :param number: Number of Triggers per sequence - 1 to 100000 or 2147483647 (INF)
        :type number: int
        :param interval: Timing interval in seconds - must be greater than 20E-6
        :type interval: float
        :param delay: Delay before first trigger in seconds
        :type delay: float 
        """
        validTriggers = ['AINT', 'BUS', 'TIMER', 'INT1', 'INT2', 'LAN', 'EXT1', 'EXT2',
            'EXT3', 'EXT4', 'EXT5', 'EXT6', 'EXT7', 'EXT8', 'EXT9', 'EXT10',
            'EXT11', 'EXT12', 'EXT13', 'EXT14']

        if triggerSource in validTriggers:
            self.write(':TRIG:SOUR %s' % triggerSource)
            self.write(':TRIG:COUN %i' % number)
            
            if triggerSource == 'TIMER':
                self.write(':TRIG:TIME %f' % float(interval))
            
            if delay > 0.0:
                self.write(':TRIG:DEL %f' % float(delay))
            else:
                self.write(':TRIG:DEL 0')

    def setVoltageLimit(self, channel, limit):
        pass

    def setCurrentLimit(self, channel, limit):
        """
        Set current protection limit

        :param channel:         SMU Channel
        :type channel:          int
        :param limit:           Current limit
        :type limit:            float
        """
        self.write(":SENS{0}:CURR:PROT {1}".format(channel, limit))

    def enableHighCapacitanceOutput(self, channel):
        """
        Enables the high capacitance mode. This mode is effective for high capacitance DUT

        :param channel:         SMU Channel
        :type channel:          int
        """
        self.write(":OUTP{0}:HCAP ON".format(channel))

    def disableHighCapacitanceOutput(self, channel):
        """
        Disables the high capacitance mode.

        :param channel:         SMU Channel
        :type channel:          int
        """
        self.write(":OUTP{0}:HCAP OFF".format(channel))

    def powerOn(self):
        """
        Enable the SMU to the programmed output level
        """
        self.write(':OUTP ON')
        
    def powerOff(self):
        """
        Power off the SMU using the previously programmed power-off mode
        """
        self.write(':OUTP OFF')

    def setPowerOffMode(self, channel, mode):
        """
        Set the power off mode

          * `NORMAL` - Normal (0V, output relay off)
          * `ZERO` - Ground output (0V, output relay on)
          * `HIZ` - Float output (Floating, output relay off)

        :param channel:         SMU Channel
        :type channel:          int
        :param mode:            Power output mode
        :type mode:             str
        :return:
        """
        self.write(":OUTP{0}:OFF:MODE {1}".format(channel, mode))
        
    def setPowerOffModeZero(self, channel):
        """
        Power off the SMU, output is held at ground voltage

        :param channel:         SMU Channel
        :type channel:          int
        """
        self.setPowerOffMode(channel, 'ZERO')
        
    def setPowerOffModeFloat(self, channel):
        """
        Power off the SMU, output is left floating

        :param channel:         SMU Channel
        :type channel:          int
        """
        self.setPowerOffMode(channel, 'HIZ')

    def trigger(self, channel):
        pass
        
    def startProgram(self, channel=1):
        """
        Start a program sequence / Force trigger.
        
        :param channel: Channel (1 or 2)
        :type channel: int
        """
        if channel == 1:
            self.write(':INIT (@1)')
            
        elif channel == 2:
            self.write(':INIT (@2)')

    #===========================================================================
    # Helper Functions
    #===========================================================================
    
    def rampVoltage(self, startVoltage, stopVoltage, time, delay=0):
        """
        Automated voltage ramp
        
        :param startVoltage: Starting Voltage
        :type startVoltage: float
        :param stopVoltage: Stop Voltage
        :type stopVoltage: float
        :param time: Rise/Fall Time (seconds)
        :type time: float
        :param delay: Time (seconds) before ramp is started
        :type delay: float
        """
        if float(time) < 0.05:
            # Minimum Interval
            interval = 20E-6
            points = int(float(time) / interval)
        
        else:
            # Maximum resolution
            points = 2500
            interval = float(time) / float(points)
        
        #interv = float(time) / float(points)
        
        # Set default parameters and enable
        self.setSourceFixed('VOLTAGE', startVoltage, startVoltage)
        self.powerOn()
        
        # Setup sweep params
        self.setSourceSweep('VOLTAGE', startVoltage, stopVoltage, points)
        
        self.setTriggerSetup('TIMER', points, interval, delay)
        
        self.write(":SOUR:FUNC:TRIG:CONT ON") # OUTPUT AFTER SWEEP - END VAL
        self.startProgram(1)

    def sampleMeasurements(self, channel, numSamples, sampleTime, startDelay):
        pass

    def setSourceSweep(self, source, start, stop, points):
        """
        Configure the SMU to Sweep a range of points.

        :param source: Voltage or Current Source - ['VOLTAGE', 'CURRENT']
        :type source: str
        :param start: Starting Voltage/Current
        :type start: float
        :param stop: Final Voltage/Current
        :type stop: float
        :param points: Number of Points
        :type points: int
        """
        if source in self.validSource.keys():
            source_f = self.validSource.get(source)
            self.write(':SOUR:FUNC:MODE %s' % source_f)
            self.write(':SOUR:%s:MODE SWE' % source_f)

            self.write(':SOUR:%s:START %f' % (source_f, float(start)))
            self.write(':SOUR:%s:STOP %f' % (source_f, float(stop)))

            # Hard-coded number of points
            # It appears the length of the sweep is determined by the number
            # of points
            self.write(':SOUR:SWE:POIN %i' % int(points))
            self.write(':TRIG:COUN %i' % int(points))

            if float(stop) > float(start):
                self.write(':SOUR:SWE:DIR UP')
            else:
                self.write(':SOUR:SWE:DIR DOWN')

    def setSourceFixed(self, source, base, peak):
        """
        Configure the SMU to output a fixed voltage or current

        :param source: Voltage or Current Source - ['VOLTAGE', 'CURRENT']
        :type source: str
        :param base: Base Voltage/Current
        :type base: float
        :param peak: Peak Voltage/Current when triggered
        :type peak: float
        """
        if source in self.validSource.keys():
            source_f = self.validSource.get(source)
            self.write(':SOUR:FUNC:MODE %s' % source_f)

            self.write(':SOUR:%s %f' % (source_f, float(base)))
            self.write(':SOUR:%s:TRIG %f' % (source_f, float(peak)))

    def setSourceProgram(self):
        # TODO
        pass

    def setPulseSetup(self, pulseEnable, pulseWidth, delay=0.0):
        """
        Set SMU Pulse settings

        :param pulseEnable: Enable/Disable Pulsing
        :type pulseEnable: bool
        :param pulseWidth: Pulse width in seconds - must be greater than 20E-6
        :type pulseWidth: float
        :param delay: Delay before first pulse in seconds
        :type delay: float
        """
        if pulseEnable:
            self.write(':SOUR:FUNC:SHAP PULS')

            self.write(':SOUR:PULS:WIDT %f' % float(pulseWidth))

            if delay > 0.0:
                self.write(':SOUR:PULS:DEL %f' % float(delay))

        else:
            self.write(':SOUR:FUNC:SHAP DC')