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
        
    def setSourceSweep(self, source, start, stop, **kwargs):
        """
        Configure the SMU to Sweep a range of points.
        
        :param source: Voltage or Current Source - ['VOLTAGE', 'CURRENT']
        :type source: str
        :param start: Starting Voltage/Current
        :type start: float
        :param stop: Final Voltage/Current
        :type stop: float
        
        :param Pulse: Enable/Disable Pulsing
        :type Pulse: bool
        :param Width: Pulse Width in sec (Pulsing Enabled only)
        :type Width: float
        :param Delay: Pulse Delay in sec (Pulsing Enabled only)
        :type Delay: float
        :param TriggerDelay: Trigger Delay in sec
        :type TriggerDelay: float
        :param TriggerInterval: Trigger Interval in sec
        :type TriggerInterval: float
        """
        if source in self.validSource.keys():
            source_f = self.validSource.get(source)
            self.write(':SOUR:FUNC:MODE %s' % source_f)
            self.write(':SOUR:%s:MODE SWE' % source_f)

            self.write(':SOUR:%s:START %f' % (source_f, float(start)))
            self.write(':SOUR:%s:STOP %f' % (source_f, float(stop)))
            
            # Hard-coded number of points
            self.write(':SOUR:SWE:POIN %i' % 2500)
                        
            if float(stop) > float(start):
                self.write(':SOUR:SWE:DIR UP')
            else:
                self.write(':SOUR:SWE:DIR DOWN')
                
            self.setSourceSetup(**kwargs)            
        
    def setSourceFixed(self, source, base, peak, **kwargs):
        """
        Configure the SMU to output a fixed voltage or current
        
        :param source: Voltage or Current Source - ['VOLTAGE', 'CURRENT']
        :type source: str
        :param base: Base Voltage/Current
        :type base: float
        :param peak: Peak Voltage/Current
        :type peak: float
        
        :param Pulse: Enable/Disable Pulsing
        :type Pulse: bool
        :param Width: Pulse Width in sec (Pulsing Enabled only)
        :type Width: float
        :param Delay: Pulse Delay in sec (Pulsing Enabled only)
        :type Delay: float
        :param TriggerDelay: Trigger Delay in sec
        :type TriggerDelay: float
        :param TriggerInterval: Trigger Interval in sec
        :type TriggerInterval: float
        """
        if source in self.validSource.keys():
            source_f = self.validSource.get(source)
            self.write(':SOUR:FUNC:MODE %s' % source_f)
            
            self.write(':SOUR:%s %f' % (source_f, float(base)))
            self.write(':SOUR:%s:TRIG %f' % (source_f, float(peak)))
        
            self.setSourceSetup(**kwargs)
            
    def setSourceProgram(self):
        pass
        
    def setSourceSetup(self, **kwargs):
        """
        Set SMU Source Trigger and Pulse parameters.
        
        :param Pulse: Enable/Disable Pulsing
        :type Pulse: bool
        :param Width: Pulse Width in sec (Pulsing Enabled only)
        :type Width: float
        :param Delay: Pulse Delay in sec (Pulsing Enabled only)
        :type Delay: float
        :param TriggerDelay: Trigger Delay in sec
        :type TriggerDelay: float
        :param TriggerInterval: Trigger Interval in sec
        :type TriggerInterval: float
        """
        if 'Pulse' in kwargs:
            if bool(kwargs.get('Pulse', False)):
                self.write(':SOUR:FUNC:SHAP PULS')
                
                if 'Width' in kwargs:
                    self.write(':SOUR:PULS:WIDT %f' % float(kwargs['Width']))
                    
                if 'Delay' in kwargs:
                    self.write(':SOUR:PULS:DEL %f' % float(kwargs['Delay']))
            
            else:
                self.write(':SOUR:FUNC:SHAP DC')
                
        if 'TriggerDelay' in kwargs:
            self.write(':TRIG:DEL %f' % float(kwargs['TriggerDelay']))
        else:
            self.write(':TRIG:DEL 0')
            
        if 'TriggerInterval' in kwargs:
            self.write(':TRIG:SOUR TIMER')
            self.write(':TRIG:TIME %f' % float(kwargs['TriggerInterval']))
            self.write(':TRIG:COUN %i' % int(kwargs.get('Points', 2500)))
        else:
            self.write(':TRIG:SOUR AINT')
    
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
    
    def rampVoltage(self, startVoltage, stopVoltage, time, points):
        """
        Sweep through a list of programmed points and take measurements at each
        point.
        
        Uses:
        - Voltage ramp rates
        
        Parameters
        - Source: VOLT or CURR (Default: VOLT)
        """
        interv = float(time) / float(points)
        
        setSourceSweep('VOLTAGE', startVoltage, stopVoltage,
                       Points=points,
                       TriggerInterval=interv )
    

    