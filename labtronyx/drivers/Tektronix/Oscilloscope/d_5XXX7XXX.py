from Base_Driver import Base_Driver

import time
import struct
import base64
import csv
import sys

import numpy

class d_5XXX7XXX(Base_Driver):
    
    info = {
        # Model revision author
        'author':               'KKENNEDY',
        # Model version
        'version':              '1.0',
        # Revision date of Model version
        'date':                 '2015-01-31',
        # Device Manufacturer
        'deviceVendor':         'Tektronix',
        # List of compatible device models
        'deviceModel':          [ # DPO2XXX Series
                    
                                # DPO3XXX Series
                                "DPO2024", # TODO: Verify this driver works for this model
                                # DPO4XXX Series
                                
                                # DPO5XXX Series
                                "DPO5054", "DPO5054B", "DPO5104", "DPO5104B", 
                                "DPO5204", "DPO5204B", "DPO5034", "DPO5034B",
                                # DPO7XXX Series
                                "DPO7054C", "DPO7104C", "DPO7254C", "DPO7354C",
                                # DPO7XXXX Series
                                "DPO70404C", "DPO70604C", "DPO70804C", 
                                "DPO71254C", "DPO71604C", "DPO72004C", 
                                "DPO72304DX", "DPO72504DX", "DPO73304DX"],
        # Device type    
        'deviceType':           'Oscilloscope',      
        
        # List of compatible resource types
        'validResourceTypes':   ['VISA'],  
        
        #=======================================================================
        # VISA Attributes        
        #=======================================================================
        # Compatible VISA Manufacturers
        'VISA_compatibleManufacturers': ['TEKTRONIX', 'Tektronix'],
        # Compatible VISA Models
        'VISA_compatibleModels':        ["DPO2024"
                                         "DPO5054", "DPO5054B", "DPO5104", 
                                         "DPO5104B", "DPO5204", "DPO5204B", 
                                         "DPO5034", "DPO5034B", "DPO7054C", 
                                         "DPO7104C", "DPO7254C", "DPO7354C", 
                                         "DPO70404C", "DPO70604C", "DPO70804C", 
                                         "DPO71254C", "DPO71604C", "DPO72004C", 
                                         "DPO72304DX", "DPO72504DX", "DPO73304DX"
                                         ]
    }
    
    # Device Specific constants
    validWaveforms = ['CH1', 'CH2', 'CH3', 'CH4', 'REF1', 'REF2', 'REF3', 'REF4', 'MATH1', 'MATH2', 'MATH3', 'MATH4']
    validTriggerTypes = ['EDGE', 'TRANSITION']
    validCursorTypes = ['HBARS', 'VBARS', 'SCREEN', 'WAVEFORM', 'XY']

    def _onLoad(self):
        self.instr = self.getResource()
        
        self.instr.open()
        
        # Configure scope
        self.instr.write('HEADER OFF')
        resp = str(self.instr.query('HEADER?')).strip()
        if resp != '0':
            time.sleep(1.0)
            self.instr.write('HEADER OFF')
            
        self.data = {}
        
    def _onUnload(self):
        pass
        
    def defaultSetup(self):
        """
        Resets the Oscilloscope to the Default Setup
        """
        self.instr.write("FAC")
        
        # TODO: Make this not a static delay
        time.sleep(1.0)
        
        self._onLoad()
        
    def getEnabledWaveforms(self):
        """
        Get a list of the enabled waveforms.
        
        Example::
        
            >> scope.getEnabledWaveforms()
            ['CH1', 'CH3']
        
        :returns: list
        """
        en_ch = []
        
        for ch in self.validWaveforms:
            resp = self.instr.query('SELECT:' + ch + '?')
            if int(resp):
                en_ch.append(ch)
        
        return en_ch
    
    def setAcquisitionSetup(self, **kwargs):
        """
        Set Acquisition Modes
        
        .. note::
        
            Not all features are available on all models
            
        :param State: Run state - ['SINGLE', 'OFF', 'ON', 'RUN', 'STOP']
        :type State: str
        :param FastAcq: Fast Acquisition Mode - ['ON', 'OFF']
        :type FastAcq: str
        :param MagniVu: MagniVu Mode - ['ON', 'OFF']
        :type MagniVu: str
        :param Mode: Operating Mode - ['Sample', 'PeakDetect', 'HighResolution', 'Average', 'WaveformDB', 'Envelope']
        :type Mode: str
        :param Number: Number of samples when Mode is 'Average' or 'Envelope'
        :type Number: int
        :param RollMode: Horizontal Roll Mode - ['AUTO', 'ON', 'OFF']
        :type RollMode: str
        :param SamplingMode: Sampling Mode - ['RealTime', 'Equivalent', 'Interpolate']
        :type SamplingMode: str
        
        Operating Modes::
        
            'Sample' specifies that the displayed data point value is the first sampled value
            that is taken during the acquisition interval. In sample mode, all waveform data
            has 8 bits of precision. You can request 16 bit data with a CURVe query but the
            lower-order 8 bits of data will be zero. SAMple is the default mode.
            
            'PeakDetect' specifies the display of high-low range of the samples taken from a
            single waveform acquisition. The high-low range is displayed as a vertical column
            that extends from the highest to the lowest value sampled during the acquisition
            interval. PEAKdetect mode can reveal the presence of aliasing or narrow spikes.
            
            'HighResolution' specifies Hi Res mode where the displayed data point value is the
            average of all the samples taken during the acquisition interval. This is a form
            of averaging, where the average comes from a single waveform acquisition. The number 
            of samples taken during the acquisition interval determines the number of
            data values that compose the average.
            
            'Average' specifies averaging mode, in which the resulting waveform shows an
            average of SAMple data points from several separate waveform acquisitions. The
            instrument processes the number of waveforms you specify into the acquired
            waveform, creating a running exponential average of the input signal. The number
            of waveform acquisitions that go into making up the average waveform is set or
            queried using the ACQuire:NUMEnv command.
            
            'WaveformDB' (Waveform Database) mode acquires and displays a waveform pixmap. A
            pixmap is the accumulation of one or more acquisitions.
            
            'Envelope' specifies envelope mode, where the resulting waveform shows the
            PeakDetect range of data points from several separate waveform acquisitions.
            The number of waveform acquisitions that go into making up the envelope
            waveform is set or queried using the ACQuire:NUMEnv command.
            
            The instrument acquires data after each trigger event using Sample mode; it then
            determines the pix map location of each sample point and accumulates it with
            stored data from previous acquisitions.
            A Pix map is a two dimensional array. The value at each point in the array is
            a counter that reflects the hit intensity. Infinite and noninfinite persist display
            modes affect how pix maps are accumulated. Zoom, Math, FastAcq, FastFrame,
            XY, Roll, and Interpolated Time (IT) Sampling Mode are conflicting features to
            WFMDB acqMode. Turning on one of them generally turns the other one off.
            Selection of some standard masks (for example, eye masks, which require option
            MTM) changes the acquisition mode to WFMDB.
        """
        
        if 'State' in kwargs:
            if kwargs['State'] == 'SINGLE':
                self.instr.write("ACQ:STOPAFTER SEQUENCE")
                self.instr.write("ACQ:STATE 1")
            else:
                self.instr.write('ACQ:STOPAFTER RUNSTOP')
                self.instr.write('ACQ:STATE ' + str(kwargs['State']))
                
        if 'FastAcq' in kwargs:
            self.instr.write('FASTACQ:STATE ' + str(kwargs['FastAcq']))
            
        if 'MagniVu' in kwargs:
            self.instr.write('ACQ:MAGNIVU ' + str(kwargs['MagniVu']))
        
        if 'Mode' in kwargs:
            
            if kwargs['Mode'] == 'Sample':
                self.instr.write('ACQ:MODE SAMPLE')
                
            elif kwargs['Mode'] == 'PeakDetect':
                self.instr.write('ACQ:MODE PEAK')
                
            elif kwargs['Mode'] == 'HighResolution':
                self.instr.write('ACQ:MODE HIRES')
                
            elif kwargs['Mode'] == 'Average':
                self.instr.write('ACQ:MODE AVERAGE')
                if 'Number' in kwargs:
                    self.instr.write('ACQ:NUMAVG ' + str(kwargs['Number']))
                
            elif kwargs['Mode'] == 'WaveformDB':
                self.instr.write('ACQ:MODE WFMDB')
                
            elif kwargs['Mode'] == 'Envelope':
                self.instr.write('ACQ:MODE ENV')
                if 'Number' in kwargs:
                    self.instr.write('ACQ:NUMENV ' + str(kwargs['Number']))
                
        if 'RollMode' in kwargs:
            self.instr.write('HOR:ROLL ' + str(kwargs['RollMode']))
        
        if 'SamplingMode' in kwargs:
            if kwargs['SamplingMode'] == 'RealTime':
                self.instr.write('ACQ::SAMPLINGMODE RT')
            elif kwargs['SamplingMode'] == 'Equivalent':
                self.instr.write('ACQ::SAMPLINGMODE ET')
            elif kwargs['SamplingMode'] == 'Interpolate':
                self.instr.write('ACQ::SAMPLINGMODE IT')
                
    def setCursorSetup(self, **kwargs):
        """
        Set cursor configuration.
        
        :param Type: Cursor Type - ['HBARS', 'VBARS', 'SCREEN', 'WAVEFORM']
        :type Type: str
        :param Display: Display Cursors - ['ON', 'OFF']
        :type Display: str
        :param Mode: Cursor Mode - ['Track', 'Independent']
        :type Mode: str
        :param LineStyle: Cursor Line Style - ['DASHED', 'SDASHED', 'SOLID']
        :type LineStyle: str
        :param Source1: Waveform for Source1 - ['CH1', 'CH2', 'CH3', 'CH4', 'MATH1', 'MATH2', 'MATH3', 'MATH4', 'REF1', 'REF2', 'REF3', 'REF4']
        :type Source1: str
        :param Source2: Waveform for Source2 - ['CH1', 'CH2', 'CH3', 'CH4', 'MATH1', 'MATH2', 'MATH3', 'MATH4', 'REF1', 'REF2', 'REF3', 'REF4']
        :type Source2: str
        :param Pos1: Pos1 in 'HBARS', 'VBARS' or 'WAVEFORM' Mode
        :type Pos1: int or float
        :param Pos2: Pos2 in 'HBARS', 'VBARS' or 'WAVEFORM' Mode
        :type Pos2: int or float
        :param X1: X1 in 'SCREEN' Mode
        :type X1: int or float
        :param X2: X2 in 'SCREEN' Mode
        :type X2: int or float
        :param Y1: Y1 in 'SCREEN' Mode
        :type Y1: int or float
        :param Y2: Y2 in 'SCREEN' Mode
        :type Y2: int or float
        :param Style: Cursor Style in 'SCREEN' Mode - ['LINE_X', 'LINES', 'X']
        :type Style: str
        :returns: bool - True if successful, False otherwise
        """
        if 'Type' in kwargs and kwargs['Type'] in m_OscilloscopeBase.validCursorTypes:
            if 'Display' in kwargs:
                self.instr.write('CURS:STATE ' + str(kwargs['Display']))
            if 'Mode' in kwargs:
                self.instr.write('CURS:MODE ' + str(kwargs['Mode']))
            if 'Type' in kwargs:
                self.instr.write('CURS:FUNC ' + str(kwargs['Type']))
            if 'LineStyle' in kwargs:
                self.instr.write('CURS:LINESTYLE ' + str(kwargs['LineStyle']))
            if 'Source1' in kwargs and kwargs['Source1'] in m_OscilloscopeBase.validWaveforms:
                self.instr.write('CURS:SOURCE1 ' + kwargs['Source1'])
            if 'Source2' in kwargs and kwargs['Source2'] in m_OscilloscopeBase.validWaveforms:
                self.instr.write('CURS:SOURCE2 ' + kwargs['Source2'])
                    
            # Cursor Types
            # Horizontal Bars
            if kwargs['Type'] == 'HBARS':  
                if 'Pos1' in kwargs:
                    self.instr.write('CURS:HBARS:POS1 ' + str(float(kwargs['Pos1'])))
                if 'Pos2' in kwargs:
                    self.instr.write('CURS:HBARS:POS2 ' + str(float(kwargs['Pos2'])))   
            # Vertical Bars
            elif kwargs['Type'] == 'VBARS':
                if 'Pos1' in kwargs:
                    self.instr.write('CURS:VBARS:POS1 ' + str(float(kwargs['Pos1'])))
                if 'Pos2' in kwargs:
                    self.instr.write('CURS:VBARS:POS2 ' + str(float(kwargs['Pos2']))) 
            # Screen
            elif kwargs['Type'] == 'SCREEN':
                if 'X1' in kwargs:
                    self.instr.write('CURS:SCREEN:XPOSITION1 ' + str(float(kwargs['X1'])))
                if 'X2' in kwargs:
                    self.instr.write('CURS:SCREEN:XPOSITION2 ' + str(float(kwargs['X2']))) 
                if 'Y1' in kwargs:
                    self.instr.write('CURS:SCREEN:YPOSITION1 ' + str(float(kwargs['Y1'])))
                if 'Y2' in kwargs:
                    self.instr.write('CURS:SCREEN:YPOSITION2 ' + str(float(kwargs['Y2']))) 
                if 'Style' in kwargs:
                    self.instr.write('CURS:SCREEN:STYLE ' + str(float(kwargs['Style'])))
            # Waveform
            elif kwargs['Type'] == 'WAVEFORM':
                if 'Pos1' in kwargs:
                    self.instr.write('CURS:WAVE:POS1 ' + str(float(kwargs['Pos1'])))
                if 'Pos2' in kwargs:
                    self.instr.write('CURS:WAVE:POS2 ' + str(float(kwargs['Pos2'])))   
                if 'Style' in kwargs:
                    self.instr.write('CURS:WAVEFORM:STYLE ' + str(float(kwargs['Style'])))
            elif kwargs['Type'] == 'XY':
                # TODO
                pass
                    
        else:
            self.logger.error('Must specify cursor Type')
            return False
    
        return True
    
        # TODO: Make this not a static delay
        time.sleep(1.0)
    
    def setHorizontalSetup(self, **kwargs):
        """
        Set Horizontal configuration
        
        :param Mode: Horizontal Mode - ['AUTO', 'CONSTANT', 'MANUAL']
        :type Mode: str
        :param SampleRate: Samples per second
        :type SampleRate: float
        :param Scale: Horizontal scale
        :type Scale: float
        :param Position: Horizontal Position - Percentage of screen
        :type Position: int between 0-100
        """
        if 'Mode' in kwargs:
            self.instr.write('HOR:MODE ' + kwargs['Mode'])
        if 'SampleRate' in kwargs:
            self.instr.write('HOR:MODE:SAMPLERATE ' + str(float(kwargs['SampleRate'])))
        if 'Scale' in kwargs:
            self.instr.write('HOR:MODE:SCALE ' + str(float(kwargs['Scale'])))
        if 'Position' in kwargs:
            self.instr.write('HOR:POS ' + str(float(kwargs['Position'])))
        # TODO: Implement:
        # Units
        # Delay
        # Record Length
        # Roll Mode
        
    def setVerticalSetup(self, **kwargs):
        """
        Set Vertical Configuration
        
        :param Waveform: Channel - ['CH1', 'CH2', 'CH3', 'CH4', 'REF1', 'REF2', 'REF3', 'REF4', 'MATH1', 'MATH2', 'MATH3', 'MATH4']
        :type Waveform: str
        :param Display: Display Channel - ['ON', 'OFF']
        :type Display: str
        :param Label: Channel Label
        :type Label: str
        :param Position: Vertical Position of channel - divisions above or below center
        :type Position: float
        :param Scale: Channel Vertical scale
        :type Scale: float
        :param Coupling: Input Attenuator Coupling Setting - ['AC', 'DC', 'DCREJECT', 'GND']
        :type Coupling: str
        :param Deskew: Channel Deskew time (seconds)
        :type Deskew: float
        :param Bandwidth: Low-Pass Bandwidth Limit Filter (Megahertz) - ['FIVE', 'FULL', 'TWENTY', 'ONEFIFTY', 'TWOFIFTY']
        :type Bandwidth: str
        """
        if 'Waveform' in kwargs:
            if kwargs['Waveform'] not in m_OscilloscopeBase.validWaveforms:
                return False
            
            # Channel Config
            if kwargs['Waveform'][0:2] == 'CH':
                ch = kwargs['Waveform']
                
                if 'Display' in kwargs:
                    self.instr.write('SELECT:' + ch + ' ' + kwargs['Display'])
                if 'Label' in kwargs:
                    self.instr.write(ch + ':LABEL:NAME ' + '"' + kwargs['Label'] + '"')
                if 'Position' in kwargs:
                    self.instr.write(ch + ':POS ' + str(float(kwargs['Position'])))
                if 'Scale' in kwargs:
                    self.instr.write(ch + ':SCALE ' + str(float(kwargs['Scale'])))
                if 'Coupling' in kwargs:
                    self.instr.write(ch + ':COUP ' + str(kwargs['Coupling']))
                if 'Deskew' in kwargs:
                    self.instr.write(ch + ':DESKEW ' + str(kwargs['Deskew']))
                if 'Bandwidth' in kwargs:
                    self.instr.write(ch + ':BAND ' + str(kwargs['Bandwidth']))
            
            # Reference Config
            if kwargs['Waveform'][0:3] == 'REF':
                pass
            
    def getProbeInformation(self, **kwargs):
        """
        Get Probe Data
        
        :param Waveform: Channel - ['CH1', 'CH2', 'CH3', 'CH4']
        :type Waveform: str
        :returns: dict
        
        Returned data has the following keys:
        
            * 'Type' - Probe Type
            * 'Serial' - Serial Number
            * 'Range' - Attenuation Range
            * 'Resistance' - Probe Resistance
            * 'Units' - Measurement Units (Volts or Amps)
        """
        output = {}
        
        if 'Channel' in kwargs and kwargs['Channel'] in m_OscilloscopeBase.validWaveforms:
            output['Type'] = self.instr.query(kwargs['Channel'] + ':PROBE:ID:TYPE?')
            output['Serial'] = self.instr.query(kwargs['Channel'] + ':PROBE:ID:SER?')
            output['Range'] = self.instr.query(kwargs['Channel'] + ':PROBE:RANGE?')
            output['Resistance'] = self.instr.query(kwargs['Channel'] + ':PROBE:RES?')
            output['Units'] = self.instr.query(kwargs['Channel'] + ':PROBE:UNITS?')
            
        return output
            
    def setTriggerSetup(self, **kwargs):
        """
        Set Trigger Configuration
        
        .. note::
        
            Only a small subset of the trigger types are supported right now.
        
        :param Type: Trigger Type - ['EDGE', 'TRANSITION']
        :type Type: str
        :param Source: Trigger Source - ['CH1', 'CH2', 'CH3', 'CH4', 'REF1', 'REF2', 'REF3', 'REF4', 'MATH1', 'MATH2', 'MATH3', 'MATH4']
        :type Source: str
        :param Slope: Edge to trigger on - ['RISE', 'FALL', 'EITHER']
        :type Slope: str
        :param Level: Level to trigger on
        :type Level: float
        """
        if 'Type' in kwargs and kwargs['Type'] in m_OscilloscopeBase.validTriggerTypes:
            if kwargs['Type'] == 'EDGE':
                if 'Source' in kwargs and kwargs['Source'] in m_OscilloscopeBase.validWaveforms:
                    self.instr.write('TRIG:A:EDGE:SOURCE ' + kwargs['Source'])
                if 'Slope' in kwargs:
                    self.instr.write('TRIG:A:EDGE:SLOPE ' + kwargs['Slope'])
                if 'Level' in kwargs:
                    self.instr.write('TRIG:A:LEVEL:' + kwargs['Source'] + ' ' + str(kwargs['Level']))
        
                    
    def setSearchSetup(self, **kwargs):
        """
        Set Search configuration
        
        :param Search: Search slot number
        :type Search: int between 1-8
        :param Type: Search type - ['TRANSITION']
        :type Type: str
        :param Enable: Enable Search - ['OFF', 'ON']
        :type Enable: str
        :returns: bool - True if successful, False otherwise
        
        .. note::
        
            Only 'TRANSITION' Search Type is supported right now. 
            The full range of possible Search Types are:
            ['EDGE', 'RUNT', 'TRANSITION', 'PATTERN', 'GLITCH', 'SETHOLD', 'UNDEFINED', WIDTH', 'TIMEOUT', 'WINDOW', 'STATE', 'DDRREAD', 'DDRWRITE', 'DDRREADWRITE']
        
        Parameters for 'TRANSITION' Search Type:
        
            * 'Source' (str) - Channel source to search - ['CH1', 'CH2', 'CH3', 'CH4', 'REF1', 'REF2', 'REF3', 'REF4', 'MATH1', 'MATH2', 'MATH3', 'MATH4']
            * 'Delta' (float) - Time delta to limit matches
            * 'HighThreshold' (float) - High Threshold level
            * 'LowThreshold' (float) - Low Threshold level
            * 'Slope' (str) - Polarity setting for mark placement - ['EITHER', 'NEGATIVE', 'POSITIVE']
            * 'Transition' (str) - Transition Trigger Condition - ['FASTERTHAN', 'SLOWERTHAN'] 
        
        """
        if 'Search' in kwargs and int(kwargs['Search']) in range(1,8):
            if 'Type' in kwargs and kwargs['Type'] in m_OscilloscopeBase.validTriggerTypes:
                if 'Enable' in kwargs:
                    self.instr.write('SEARCH:SEARCH' + str(kwargs['Search']) + ':STATE ' + kwargs['Enable'])
                    # TODO: Is this the right place for this?
                    self.instr.write("SEARCH:MARKALL ON")
                
                self.instr.write('SEARCH:SEARCH' + str(kwargs['Search']) + ':TRIG:A:TYPE ' + kwargs['Type'])
                
                # Trigger Types
                # Transition
                if kwargs['Type'] == 'TRANSITION':
                    if 'Source' in kwargs and kwargs['Source'] in m_OscilloscopeBase.validWaveforms:
                        self.instr.write('SEARCH:SEARCH' + str(kwargs['Search']) + ':TRIG:A:PULSE:SOURCE ' + str(kwargs['Source']))
                    if 'Delta' in kwargs:
                        self.instr.write('SEARCH:SEARCH' + str(kwargs['Search']) + ':TRIG:A:TRAN:DELTATIME ' + str(kwargs['Delta']))
                    if 'HighThreshold' in kwargs:
                        self.instr.write('SEARCH:SEARCH' + str(kwargs['Search']) + ':TRIG:A:TRAN:THR:HIGH:' + str(kwargs['Source']) + ' ' + str(kwargs['HighThreshold']))
                    if 'LowThreshold' in kwargs:
                        self.instr.write('SEARCH:SEARCH' + str(kwargs['Search']) + ':TRIG:A:TRAN:THR:LOW:' + str(kwargs['Source']) + ' ' + str(kwargs['LowThreshold']))
                    if 'Slope' in kwargs:
                        self.instr.write('SEARCH:SEARCH' + str(kwargs['Search']) + ':TRIG:A:TRAN:POL:' + str(kwargs['Source']) + ' ' + str(kwargs['Slope']))
                    if 'Transition' in kwargs:
                        self.instr.write('SEARCH:SEARCH' + str(kwargs['Search']) + ':TRIG:A:TRAN:WHEN ' + str(kwargs['Transition']))
                
            else:
                self.logger.error('Must specify valid Search Type')
                return False
        else:
            self.logger.error('Must specify Search between 1-8')
            return False
        
        # TODO: Make this not a static delay
        time.sleep(5.0)
        
        return True
        
    
    def getSearchMarks(self, **kwargs):
        """
        Get a list of all mark locations. Manually iterates through all marks
        on the oscilloscope and gets the location.
        
        .. warning::
        
            Depending on the number of marks, this function can take some time
            to complete
            
        :param Search: Search slot number
        :type Search: int between 1-8
        :returns: list of mark times (float)
        """
        # TODO: More graceful way of doing this
        if self.waitUntilReady(1.0, 10.0):
            
            if 'Search' in kwargs and int(kwargs['Search']) in range(1,8):
                self.logger.debug('Looking for matches')
                
                matches = int(self.instr.query('SEARCH:SEARCH' + str(int(kwargs['Search'])) + ':TOTAL?'))
                total_marks = int(self.instr.query("MARK:TOTAL?"))
                
                hor_scale = float(self.instr.query('HOR:MODE:SCALE?'))
                hor_pos = float(self.instr.query('HOR:POS?'))
                
                all_marks = []
                search_marks = []
                
                if matches > 0:
                    self.logger.debug("Expecting %i marks", matches)
                    # Convert the search marks to user marks
                    self.instr.write('SEARCH:SEARCH' + str(kwargs['Search']))
                    
                    # Seek Forward
                    for dir in ['NEXT', 'PREV']:
                        for i in range(1,total_marks+1):
                            if  len(search_marks) < matches:
                                mark_start = float(str(self.instr.query('MARK:SELECTED:START?')).strip())
                                
                                if mark_start not in all_marks:
                                    mark_owner = str(self.instr.query('MARK:SELECTED:OWNER?')).strip()
                                    seek_owner = 'SEARCH' + str(kwargs['Search'])
                                    if mark_owner == seek_owner:
                                        # Convert from percentage to time
                                        mark_start = (mark_start - hor_pos) * (hor_scale / 10.0)
                                        
                                        search_marks.append(mark_start)
                                        self.logger.debug("Search Mark Found at " + str(mark_start))
                                        
                                all_marks.append(mark_start)
                                
                                self.logger.debug("Mark Seek " + dir)
                                self.instr.write('MARK ' + dir)
                                
                                time.sleep(1.0)
                                
                        # Exit out of zoom mode
                        self.instr.write("ZOOM:MODE OFF")
                        
                        time.sleep(1.0)
                else:
                    self.logger.debug('No matches found')
                    
                return search_marks
            
            else:
                self.logger.error('Must specify Search between 1-8')
                return []
        else:
            self.logger.error("Unable to get marks while oscilloscope is busy")
            return []

        
    def singleAcquisition(self):
        """
        Put the Oscilloscope into Single Acquisition mode
        """
        self.logger.info('Entering Single Acquisition Mode')
        self.setAcquisitionSetup(State='SINGLE')
        
    def statusBusy(self):
        """
        Queries the scope to find out if it is busy
        
        :returns: bool - True if Busy, False if not Busy
        """
        if int(self.instr.query('BUSY?')):
            self.logger.debug('Instrument is busy')
            return True
        else:
            self.logger.debug('Instrument is ready')
            return False
        
    def waitUntilReady(self, interval=1.0, timeout=10.0):
        """
        Poll the oscilloscope until ready or until `timeout` seconds has passed
        
        :param interval: Polling interval in seconds
        :type interval: float
        :param timeout: Seconds until timeout occurs
        :type timeout: float
        :returns: bool - True if instrument becomes ready, False if timeout occurs
        """
        try:
            lapsed = 0.0
            while lapsed < timeout:
                if not self.statusBusy():
                    return True
                time.sleep(interval)
                lapsed += interval
                
            self.logger.debug('Instrument was not ready before timeout occurred')
            return False
        except:
            self.logger.exception("An error occurred in waitUntilReady()")
            
    def getWaveform(self):
        """
        Refreshes the raw waveform data from the oscilloscope. 
        
        :returns: bool - True if successful, False otherwise
        """
        try:
            import numpy
            
        except:
            self.logger.error('Unable to getWaveform without numpy library')
            return False
        
        if not self.waitUntilReady(1.0, 10.0):
            self.logger.error("Unable to export waveform while oscilloscope is busy")
            return False
        
        self.logger.debug('Starting waveform transfer')
        self.data = {}
        
        # Get the list of enabled waveforms before we begin
        enabledWaveforms = self.getEnabledWaveforms()
        
        # Get time and trigger data
        x_scale = float(self.instr.query("WFMOUTPRE:XINCR?"))
        hor_scale = float(self.instr.query("HOR:MODE:SCALE?"))
        sample_rate = float(self.instr.query("HOR:MODE:SAMPLERATE?"))
        samples = int(sample_rate * hor_scale * 10)
        trigger_sample = int(self.instr.query("WFMOUTPRE:PT_OFF?"))
        
        self.data['Time'] = numpy.arange(-1 * trigger_sample, samples - trigger_sample) * x_scale
        
        self.logger.debug("Time Scale: %f", x_scale)
        self.logger.debug("Trigger position: %i", trigger_sample)
        self.logger.debug("Sample Rate: %f", sample_rate)
        self.logger.debug("Horizontal Scale: %f", hor_scale)
        self.logger.info("Expecting %i samples", samples)
        
        for ch in enabledWaveforms:
            self.instr.write("DATA:SOURCE %s" % ch)
            self.instr.write("DATA:ENC SRP")
            self.instr.write("DATA:START 1")
            self.instr.write("DATA:STOP %i" % samples)
            
            # Get scale factors for each channel
            y_scale = float(self.instr.query("WFMOUTPRE:YMULT?"))
            y_zero = float(self.instr.query("WFMOUTPRE:YZERO?"))
            y_offset = float(self.instr.query("WFMOUTPRE:YOFF?"))
            
            # Get the number of bytes per data point
            data_width = int(self.instr.query("WFMOUTPRE:BYT_NR?"))
            
            # Collect and process data
            self.logger.info("Processing Data for %s....", ch)
            self.instr.write("CURVE?")
            data_raw = self.instr.read_raw()
            
            headerlen = 2 + int(data_raw[1])
            header = data_raw[:headerlen]
            data = data_raw[headerlen:-1]
            elems = len(data) / data_width
            
            if data_width == 2:
                data = struct.unpack('%sH' % elems, data)
            elif data_width == 1:
                data = struct.unpack('%sB' % elems, data)
            else:
                self.logger.error('Unhandled data width in getWaveform')
                
            # Utilize numpy if possible, its more efficient
            data = numpy.array(data)
                
            data_scaled = (data - y_offset) * y_scale + y_zero
            
            self.data[ch] = data_scaled.tolist()
            
        return self.data
    
    
    def getPackedWaveform(self, ch):
        """
        Get packed binary waveform data for a given channel
        
        :param ch: Channel - ['CH1', 'CH2', 'CH3', 'CH4']
        :type ch: str
        :returns: binary data
        """
        if ch in self.validWaveforms and ch in self.data.keys():
            d_list = self.data.get(ch)
            points = len(d_list)
            
            # Pack the data
            packed = str(struct.pack('%sf' % points, *d_list))
            
            # Base64 Encode the data
            enc = base64.b64encode(packed)
            
            return enc
        
    def waveformExport(self, **kwargs):
        """
        Alias for :func:`m_OscilloscopeBase.exportWaveform`
        """
        return self.exportWaveform(**kwargs)
        
    def exportWaveform(self, **kwargs):
        """
        Export the oscilloscope waveform to a .csv file. 
        
        :param Filename: Filename of output file
        :type Filename: str
        :returns: bool - True if successful, False otherwise
        """
        
        # Refresh waveform data
        if self.data == {}:
            self.getWaveform()
        
        # Write data in columns in the CSV file
        if 'Filename' in kwargs:
            filename = kwargs['Filename']
            # Verify file extension
            if filename[-3:] != "csv":
                filename = filename + '.csv'
            try:
                # Open Data file
                f_telem = open(filename, 'wb')
                csvfile = csv.writer(f_telem)
                self.logger.debug("Opened file: %s", filename)
                
                intersect = set(self.validWaveforms).intersection(set(self.data.keys()))
                
                # Add an extra column for a time index
                header = ['Time'] + list(intersect)
                # Write header
                csvfile.writerow(header)
                
                # Write each row
                time = self.data['Time']
                for index in range(0, len(time)):
                    row = [time[index]]
                    for ch in intersect:
                        row.append(self.data[ch][index])
                    csvfile.writerow(row)
                f_telem.close()
                
            except:
                self.logger.exception("Unable to export data to %s" % filename)
                
                return False
                    
        return True
                
    def saveScreenshot(self, **kwargs):
        """
        Save a screenshot of the oscilloscope display onto the oscilloscope.
        
        :param Filename: Relative or absolute filename
        :type Filename: str
        :param Format: File format - ['BMP', 'JPEG', 'PCX', 'PNG', 'TIFF']
        :type Format: str
        :param Palette: Color Palette - ['COLOR', 'INKSAVER', 'BLACKANDWHITE']
        :type Palette: str
        :returns: bool - True if successful, False otherwise
        """
        
        if 'Filename' in kwargs and 'Format' in kwargs:
            
            temp_filename = kwargs['Filename'] + '.' + kwargs['Format']
            self.instr.write("EXPORT:FILENAME " + '"' + temp_filename + '"')
            self.instr.write("EXPORT:FORMAT " + kwargs['Format'])
            
            if 'Palette' in kwargs:
                self.instr.write("EXPORT:PALETTE " + kwargs['Palette'])
                
            self.instr.write("EXPORT START")
            
            # TODO: Make this not a static delay
            time.sleep(2.0)
            
            remote_filename = self.instr.query("EXPORT:FILENAME?")
            self.logger.debug('Saved remote screenshot at %s', remote_filename)
            
            return remote_filename
            
        else:
            self.logger.error("Save Screenshot needs parameters Filename and Format")
            
    def lock(self):
        """
        Lock the oscilloscope
        """
        self.instr.write('LOCK ALL')
        
    def unlock(self):
        """
        Unlock the oscilloscope
        """
        self.instr.write('UNLOCK ALL')
    