"""
.. codeauthor:: Kevin Kennedy <protonyx@users.noreply.github.com>

"""
from labtronyx.bases import DriverBase
from labtronyx.common.errors import *


class d_B29XX(DriverBase):
    """
    Driver for Agilent B2901A and B2902A Source Measurement Units
    """
    author = 'KKENNEDY'
    version = '1.0'
    deviceType = 'Source Measurement Unit'
    compatibleInterfaces = ['VISA']
    compatibleInstruments = {
        'Agilent': ['B2901A', 'B2902A']
    }

    @classmethod
    def VISA_validResource(cls, identity):
        return identity[0].upper() == 'AGILENT TECHNOLOGIES' and identity[1] in cls.compatibleInstruments['Agilent']

    VALID_SOURCE_OUTPUT_MODES = {
        'Voltage':       'VOLT',
        'Current':       'CURR'
    }

    VALID_MEASURE_MODES = {
        'Voltage':       'VOLT',
        'Current':       'CURR',
        'Resistance':    'RES'
    }

    VALID_SOURCE_MODES = {
        'Sweep': 'SWEEP',
        'Fixed': 'FIXED',
        'List':  'LIST'
    }

    VALID_TRIGGER_SOURCES = {
        'Automatic interval':   'AINT',
        'Remote':               'BUS',
        'Timer':                'TIM',
        'Internal bus 1':       'INT1',
        'Internal bus 2':       'INT2',
        'LXI':                  'LAN',
        'LAN (LXI) 0':          'LAN0',
        'LAN (LXI) 1':          'LAN1',
        'LAN (LXI) 2':          'LAN2',
        'LAN (LXI) 3':          'LAN3',
        'LAN (LXI) 4':          'LAN4',
        'LAN (LXI) 5':          'LAN5',
        'LAN (LXI) 6':          'LAN6',
        'LAN (LXI) 7':          'LAN7',
        'EXT0':                 'EXT0',
        'EXT1':                 'EXT1',
        'EXT2':                 'EXT2',
        'EXT3':                 'EXT3',
        'EXT4':                 'EXT4',
        'EXT5':                 'EXT5',
        'EXT6':                 'EXT6',
        'EXT7':                 'EXT7',
        'EXT8':                 'EXT8',
        'EXT9':                 'EXT9',
        'EXT10':                'EXT10',
        'EXT11':                'EXT11',
        'EXT12':                'EXT12',
        'EXT13':                'EXT13',
        'EXT14':                'EXT14'
    }

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
            self.getSourceOutputMode(idx)
            self.getMeasureMode(idx)

    def close(self):
        pass

    def getProperties(self):
        return dict(
            validSourceModes=self.VALID_SOURCE_MODES,
            validMeasureModes=self.VALID_MEASURE_MODES,
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

    def checkBusy(self):
        """
        Check if the instrument is busy

        :rtype: bool
        """
        return bool(self.query("*OPC?"))

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

    def _setSourceOutputMode(self, channel, output_mode='VOLT'):
        """
        Sets the source output mode.

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
        output_mode = validSource.get(output_mode, output_mode)
        output_mode = self.VALID_SOURCE_OUTPUT_MODES.get(output_mode, output_mode)

        self.write(':SOUR{0}:FUNC:MODE {1}'.format(channel, output_mode))

        # Verify
        if self.getSourceOutputMode(channel) != output_mode:
            raise RuntimeError('Set value failed verification')

    def getSourceOutputMode(self, channel):
        """
        Get the source output mode. Returns 'VOLT' (Voltage) or 'CURR' (Current)

        :param channel:         SMU Channel
        :type channel:          int
        :return:                str
        """
        mode = self.query(':SOUR{0}:FUNC:MODE?'.format(channel))
        self._mode_source[channel] = mode

        return mode

    def _setSourceMode(self, channel, mode):
        """
        Set the source mode: `FIX` - Constant current or voltage, `LIST` - User-specified list source, `SWE` - Sweep
        current or voltage

        :param channel:         SMU Channel
        :type channel:          int
        :param mode:            Source mode
        :type mode:             str
        :return:
        """
        mode = self.VALID_SOURCE_MODES.get(mode, mode)

        # Get source output mode
        outp_mode = self.getSourceOutputMode(channel)

        self.write(":SOUR{0}:{1}:MODE {2}".format(channel, outp_mode, mode))

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

        self._setSourceOutputMode(channel, 'VOLT')

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

        self._setSourceOutputMode(channel, 'CURR')

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

    def setSourceFixed(self, channel):
        """
        Set the source to fixed voltage/current mode.

        :param channel:         SMU Channel
        :type channel:          int
        """
        self._setSourceMode(channel, 'FIX')

    def setSourceSweep(self, channel, start, stop, points=2500):
        """
        Set the source to sweep mode. Must set to current or voltage mode first. Sweeps from `start` to `stop` with
        `points` number of points. Timing between each sweep point is controlled by the trigger settings. Trigger
        points should match `points`. Sweep is initiated using the `startProgram` method. To set a fixed timing between
        sweep points, consider this example::

           setTriggerSource(1, 'TIM') # Timer
           setTriggerInterval(1, 1e-3) # 1ms between sweep points
           powerOn(1)
           startProgram(1)

        :param channel:         SMU Channel
        :type channel:          int
        :param start:           Start voltage/current
        :type start:            float
        :param stop:            Stop voltage/current
        :type stop:             float
        :param points:          Points to sweep
        :type points:           int
        """
        # Sweep mode
        self._setSourceMode(channel, 'SWE')

        outp_mode = self._mode_source.get(channel)

        self.write(":SOUR{0}:{1}:START {2}".format(channel, outp_mode, start))
        self.write(":SOUR{0}:{1}:STOP {2}".format(channel, outp_mode, stop))
        self.write(":SOUR{0}:{1}:POIN {2}".format(channel, outp_mode, points))

        # Direction is UP (start -> stop)
        self.write(":SOUR{0}:SWE:DIR UP".format(channel))

    def setSourceList(self, channel, source_points=()):
        """
        Set the source to list mode. Must set to current or voltage output mode first. Timing between each point is
        controlled by the trigger settings. Trigger points should equal the number of items in `source_points`. List
        mode is initiated by using the `startProgram` method. To set a fixed timing between list points, consider this
        example::

           setTriggerSource(1, 'TIM') # Timer
           setTriggerInterval(1, 1e-3) # 1ms between sweep points
           powerOn(1)
           startProgram(1)

        :param channel:         SMU Channel
        :type channel:          int
        :param source_points:   List of points to traverse
        :type source_points:    list
        """
        # Sweep mode
        self._setSourceMode(channel, 'LIST')

        outp_mode = self._mode_source.get(channel)
        str_points = [str(x) for x in source_points]
        flat_points = ','.join(str_points)

        self.write(":SOUR{0}:LIST:{1} {2}".format(channel, outp_mode, flat_points))

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
        """
        Enable Remote Sense (4-wire) measurements

        :param channel:         SMU Channel
        :type channel:          int
        """
        self.write(":SENS{0}:REM ON".format(channel))

    def disableRemoteSense(self, channel):
        """
        Disable Remote Sense (4-wire) measurements

        :param channel:         SMU Channel
        :type channel:          int
        """
        self.write(":SENS{0}:REM OFF".format(channel))

    def setMeasurementRange(self, channel, meas_range):
        """
        Set the measurement range.

        Voltage Measurement Range
        +=============+===========================+============+
        | Range Value | Voltage Measurement Value | Resolution |
        +=============+===========================+============+
        | 0.2 V       | 0 < Voltage < 0.212       | 0.1 uV     |
        | 2.0 V       | 0 < Voltage < 2.12        | 1.0 uV     |
        | 20  V       | 0 < Voltage < 21.2        | 10  uV     |
        | 200 V       | 0 < Voltage < 212         | 100 uV     |
        +-------------+---------------------------+------------+

        Current Measurement Range
        +=============+===========================+============+
        | Range Value | Voltage Measurement Value | Resolution |
        +=============+===========================+============+
        | 100 nA      | 0 < Current < 106 nA      | 100 fA     |
        | 1 uA        | 0 < Current < 1.06 uA     | 1 pA       |
        | 10 uA       | 0 < Current < 10.6 uA     | 10 pA      |
        | 100 uA      | 0 < Current < 106 uA      | 100 pA     |
        | 1 mA        | 0 < Current < 1.06 mA     | 1 nA       |
        | 10 mA       | 0 < Current < 10.6 mA     | 10 nA      |
        | 100 mA      | 0 < Current < 106 mA      | 100 nA     |
        | 1 A         | 0 < Current < 1.06 A      | 1 uA       |
        | 1.5 A       | 0 < Current < 1.53 A      | 1 uA       |
        | 3 A         | 0 < Current < 3.06 A      | 10 uA      |
        +-------------+---------------------------+------------+

        :param channel:         SMU Channel
        :type channel:          int
        :param meas_range:      Measurement range
        :type meas_range:       float
        """
        meas_mode = self.getMeasureMode(channel)

        self.write(":SENS{0}:{1}:RANG {2}".format(channel, meas_mode, meas_range))

    def getMeasurementRange(self, channel):
        """
        Get the measurement range.

        :param channel:         SMU Channel
        :type channel:          int
        """
        meas_mode = self._mode_measure.get(channel)

        return self.query(":SENS{0}:{1}:RANG?".format(channel, meas_mode))

    def setMeasurementRangeAuto(self, channel):
        """
        Set the measurement range mode to `auto`

        :param channel:         SMU Channel
        :type channel:          int
        """
        meas_mode = self.getMeasureMode(channel)

        self.write(":SENS{0}:{1}:RANG:AUTO ON".format(channel, meas_mode))

    def getMeasurementData(self, channel):
        """
        Get the measurement data from the instrument

        :param channel:         SMU Channel
        :type channel:          int
        """
        self.write(":FORM:ELEM:SENS VOLT,CURR,TIME")

        # Use binary data format for speed
        self.write(":FORM REAL64")

        try:
            import numpy as np

            data = self.query_binary_values(":FETCH:ARR? (@{0})".format(channel), datatype='d', container=np.array)
            np.reshape(data, (3, -1))

            return data

        except ImportError:
            data = self.query_binary_values(":FETCH:ARR? (@{0})".format(channel), datatype='d')

            import itertools
            args = [iter(data)] * 3
            return list(itertools.izip_longest(*args, fillvalue=0.0))

    def setTraceBufferPoints(self, channel, data_points):
        """
        Sets the size of the instrument trace buffer. The maximum number of data points in the trace buffer is 100,000.

        :param channel:         SMU Channel
        :type channel:          int
        :param data_points:     Number of data points to record in the trace buffer
        :type data_points:      int
        """
        self.write(":TRAC{0}:POIN {1}".format(channel, data_points))

        # Verify
        if self.getTraceBufferPoints(channel) != data_points:
            raise RuntimeError('Set value failed verification')

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
        return self.query(":TRAC{0}:DATA?".format(channel))

    def setTriggerSource(self, channel, triggerSource):
        """
        Set the trigger source. See `VALID_TRIGGER_SOURCES` attribute for valid values for parameter `triggerSource`

        :param channel:         SMU Channel
        :type channel:          int
        :param triggerSource:   Trigger source
        :type triggerSource:    str
        """
        triggerSource = self.VALID_TRIGGER_SOURCES.get(triggerSource, triggerSource)

        if triggerSource not in self.VALID_TRIGGER_SOURCES.values():
            raise ValueError('Invalid Trigger Source')

        self.write(":TRIG{0}:SOUR {1}".format(channel, triggerSource))

        # Verify
        if self.getTriggerSource(channel) != triggerSource:
            raise RuntimeError('Set value failed verification')

    def getTriggerSource(self, channel):
        """
        Get current trigger source.

        :param channel:         SMU Channel
        :type channel:          int
        :return:                Trigger source
        :rtype:                 str
        """
        return self.query(":TRIG{0}:SOUR?".format(channel))

    def setTriggerSourceTimer(self, channel):
        """
        Use the timer as the trigger source

        :param channel:         SMU Channel
        :type channel:          int
        """
        self.setTriggerSource(channel, 'TIM')

    def setTriggerCount(self, channel, number):
        """
        Set the trigger count for the specified device action

        :param channel:         SMU Channel
        :type channel:          int
        :param number:          Number of triggers
        :type number:           int
        """
        self.write(":TRIG{0}:COUN {1}".format(channel, number))

        # Verify
        if self.getTriggerCount(channel) != number:
            raise RuntimeError('Set value failed verification')

    def getTriggerCount(self, channel):
        """
        Get the trigger count

        :param channel:         SMU Channel
        :type channel:          int
        """
        return self.query(":TRIG{0}:COUN?".format(channel))

    def setTriggerDelay(self, channel, delay):
        """
        Set the time delay before the first trigger

        :param channel:         SMU Channel
        :type channel:          int
        :param delay:           Trigger delay (seconds)
        :type delay:            float
        """
        self.write(":TRIG{0}:DEL {1}".format(channel, delay))

        # Verify
        if self.getTriggerDelay(channel) != delay:
            raise RuntimeError('Set value failed verification')

    def getTriggerDelay(self, channel):
        """
        Get the time delay before the first trigger

        :param channel:         SMU Channel
        :type channel:          int
        """
        return self.query(":TRIG{0}:DEL?".format(channel))

    def setTriggerInterval(self, channel, interval):
        """
        Set the time interval between triggers. `interval` is the number of seconds, must be between 1E-5 and 1E+5.

        :param channel:         SMU Channel
        :type channel:          int
        :param interval:        Trigger timer interval (seconds)
        :float interval:        float
        """
        # Requires TIMER trigger source
        self.setTriggerSource(channel, 'TIM')
        self.write(":TRIG{0}:TIME {1}".format(channel, interval))

        # Verify
        if self.getTriggerInterval(channel) != interval:
            raise RuntimeError('Set value failed verification')

    def getTriggerInterval(self, channel):
        """
        Get the time interval between triggers.

        :param channel:         SMU Channel
        :type channel:          int
        """
        return self.query(":TRIG{0}:TIME?".format(channel))

    def setVoltageLimit(self, channel, limit):
        """
        Set voltage protection limit. Automatically enables voltage protection mode

        :param channel:         SMU Channel
        :type channel:          int
        :param limit:           Voltage limit
        :type limit:            float
        """
        self.write(":SENS{0}:VOLT:PROT {1}".format(channel, limit))
        self.write(":OUTP:PROT ON")

    def setCurrentLimit(self, channel, limit):
        """
        Set current protection limit. Automatically enables current protection mode

        :param channel:         SMU Channel
        :type channel:          int
        :param limit:           Current limit
        :type limit:            float
        """
        self.write(":SENS{0}:CURR:PROT {1}".format(channel, limit))
        self.write(":OUTP:PROT ON")

    def disableOutputProtection(self):
        """
        Disable output voltage and current protection
        """
        self.write(":OUTP:PROT OFF")

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

    def powerOn(self, channel):
        """
        Enable the SMU to the programmed output level

        :param channel:         SMU Channel
        :type channel:          int
        """
        self.write(":OUTP{0} ON".format(channel))
        
    def powerOff(self, channel):
        """
        Power off the SMU using the previously programmed power-off mode

        :param channel:         SMU Channel
        :type channel:          int
        """
        self.write(":OUTP{0} OFF".format(channel))

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
        
    def startProgram(self, channel):
        """
        Start a program sequence / Force trigger.
        
        :param channel:         SMU Channel
        :type channel:          int
        """
        self.write(":INIT (@{0})".format(channel))

    #===========================================================================
    # Helper Functions
    #===========================================================================

    def getScreenshot(self, filename):
        """
        Save a screenshot of the instrument. Supported picture formats are JPG, BMP, PNG, WMF.

        :param filename:        Filename for saved screenshot
        :type filename:         str
        """
        validFormats = ['JPG', 'BMP', 'PNG', 'WMF']

        import os
        root, ext = os.path.splitext(filename)

        if ext.upper() not in validFormats:
            raise ValueError("Invalid format")

        # Set the screen dump format
        self.write(":HCOPY:SDUMP:FORM {0}".format(ext))

        # Get screen dump data
        self.write(":HCOPY:SDUMP:DATA?")
        data = self.read_raw()

        with open(filename, 'wb') as f:
            f.write(data)
    
    def rampVoltage(self, channel, startVoltage, stopVoltage, time, delay=0):
        """
        Automated voltage ramp. Enables power output, sweeps from startVoltage to stopVoltage and keeps power enabled
        after ramp is complete.

        :param channel:         SMU Channel
        :type channel:          int
        :param startVoltage:    Starting Voltage
        :type startVoltage:     float
        :param stopVoltage:     Stop Voltage
        :type stopVoltage:      float
        :param time:            Rise/Fall Time (seconds)
        :type time:             float
        :param delay:           Time (seconds) before ramp is started
        :type delay:            float
        """
        if float(time) < 0.05:
            # Minimum Interval
            interval = 20E-6
            points = int(float(time) / interval)
        
        else:
            # Maximum resolution
            points = 2500
            interval = float(time) / float(points)
        
        # Set default parameters and enable
        self.setSourceVoltage(channel, startVoltage)

        # Start power output
        self.powerOn(channel)
        
        # Setup sweep params
        self.setSourceSweep(channel, startVoltage, stopVoltage, points)

        # Setup trigger params
        self.setTriggerSourceTimer(channel)
        self.setTriggerCount(channel, points)
        self.setTriggerInterval(channel, interval)
        self.setTriggerDelay(channel, delay)

        # OUTPUT AFTER SWEEP - END VAL
        self.write(":SOUR:FUNC:TRIG:CONT ON")

        # Start program
        self.startProgram(channel)