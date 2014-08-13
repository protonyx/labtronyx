from models import m_Base

import time

class m_SMU(m_Base):
    
    deviceType = 'Source Measurement Unit'
    view = None
    
    # Model Lookup
    validControllers = ['c_VISA']
    validVIDs = ['Agilent']
    validPIDs = ['B2901A', 'B2902A']
    
    validSource = {'VOLTAGE': 'VOLT', 
                   'CURRENT': 'CURR'}
    validFunc = ['VOLT', 'CURR', 'RES']
    validMode = ['SWEEP', 'FIXED', 'LIST']
    validTrigger = ['AINT', 'BUS', 'TIMER', 'INT1', 'INT2', 'LAN', 'EXT1', 'EXT2',
                    'EXT3', 'EXT4', 'EXT5', 'EXT6', 'EXT7', 'EXT8', 'EXT9', 'EXT10',
                    'EXT11', 'EXT12', 'EXT13', 'EXT14']

    def _onLoad(self):
        self.__identity = None
        
        try:
            # Use c_VISA
            self.__instr = self.controller._getInstrument(self.resID)
            
            # Bring VISA Instrument functions into this context
            self.write = self.__instr.write
            self.read = self.__instr.read
            self.read_values = self.__instr.read_values
            self.read_raw = self.__instr.read_raw
            self.ask = self.__instr.ask
            self.ask_for_values = self.__instr.ask_for_values
            
            resp = self.ask("*IDN?")
            self.__identity = resp.strip().split(',')
            
        except:
            self.logger.exception("Internal error while attaching to VISA instrument")
    
    def getProperties(self):
        ret = m_Base.getProperties(self)
        ret['deviceVendor'] = 'Agilent'
        if self.__identity is not None:
            ret['deviceModel'] = self.__identity[1]
            ret['deviceSerial'] = self.__identity[2]
            ret['deviceFirmware'] = self.__identity[3]
            
        return ret
        
    def defaultSetup(self):
        """
        Reset the SMU to factory default settings
        """
        self.write("*RST")
        
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
        if triggerSource in self.validTrigger:
            self.write(':TRIG:SOUR %s' % triggerSource)
            self.write(':TRIG:COUN %i' % number)
            
            if triggerSource == 'TIMER':
                self.write(':TRIG:TIME %f' % float(interval))
            
            if delay > 0.0:
                self.write(':TRIG:DEL %f' % float(delay))
            else:
                self.write(':TRIG:DEL 0')
    
    def setMeasurementSetup(self, **kwargs):
        pass
    
    def powerOn(self):
        self.write(':OUTP ON')
        
    def powerOffZero(self):
        self.write(':OUTP:OFF:MODE ZERO')
        self.write(':OUTP OFF')
        
    def powerOffFloat(self):
        self.write(':OUTP:OFF:MODE HIZ')
        self.write(':OUTP OFF')
        
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
            
    def getMeasurement(self, **kwargs):
        """
        Takes a spot measurement
        """
        pass

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

    