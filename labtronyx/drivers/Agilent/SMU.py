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
    
    def setCurrentLimit(self, limit):
        """
        Set SMU current limit
        
        :param limit: Current limit
        :type limit: float
        """
        self.write(':SENS:CURR:PROT %f' % float(limit))
    
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
        
    def powerOffZero(self):
        """
        Power off the SMU, output is held at ground voltage
        """
        self.write(':OUTP:OFF:MODE ZERO')
        self.powerOff()
        
    def powerOffFloat(self):
        """
        Power off the SMU, output is left floating
        """
        self.write(':OUTP:OFF:MODE HIZ')
        self.powerOff()
        
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