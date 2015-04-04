"""
.. codeauthor:: Kevin Kennedy <kennedy.kevin@gmail.com>

Supported Interfaces
--------------------

* USB
* Ethernet (With DPO2CONN Module)

Ethernet Interface
------------------
  
If the optional `DPO2CONN Connectivity Module` is installed, these oscilloscopes
can also support Ethernet communication using the VXI extensions for VISA. The 
VISA driver should be able to detect the oscilloscope on the network.

API
---
"""
from Base_Driver import Base_Driver

import time
import struct
import base64
import csv
import sys

import numpy

class d_2XXX(Base_Driver):
    """
    Driver for Tektronix 2000 Series Oscilloscopes
    """
    
    info = {
        # Device Manufacturer
        'deviceVendor':         'Tektronix',
        # List of compatible device models
        'deviceModel':          [# MSO2XXX
                                 "MSO2002B", "MSO2004B", "MSO2012", "MSO2012B",
                                 "MSO2014", "MSO2014B", "MSO2022B",
                                 "MSO2024", "MSO2024B",
                                 # DPO2XXX
                                 "DPO2002B", "DPO2004B", "DPO2012", "DPO2012B",
                                 "DPO2014", "DPO2014B", "DPO2022B", 
                                 "DPO2024", "DPO2024B"],
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
        'VISA_compatibleModels':        ["MSO2002B", "MSO2004B", "MSO2012", 
                                         "MSO2012B", "MSO2014", "MSO2014B", 
                                         "MSO2022B", "MSO2024", "MSO2024B",
                                         "DPO2002B", "DPO2004B", "DPO2012", 
                                         "DPO2012B", "DPO2014", "DPO2014B", 
                                         "DPO2022B", "DPO2024", "DPO2024B"]
    }
    
    validWaveforms = ['CH1', 'CH2', 'CH3', 'CH4', 'REF1', 'REF2', 'MATH1']
    
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
    
    
    def getWaveform(self):
        """
        Get the waveform data from the oscilloscope
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
        
        # Record Length
        samples = int(self.instr.query("WFMO:RECO?"))
        self.logger.debug("Record Length: %i" % samples)
        
        # Time of the first point in the waveform
        t_0 = float(self.instr.query("WFMO:XZE?"))
        self.logger.debug("Time of first point: %f" % t_0)
        
        # Horizontal units
        x_scale = float(self.instr.query("WFMO:XIN?"))
        self.logger.debug("Time Scale: %f", x_scale)
        
        # Number of bytes per data point
        data_width = int(self.instr.query("WFMO:BYT_NR?"))
        
        self.data['Time'] = list(numpy.arange(t_0, samples) * x_scale)
        
        for ch in enabledWaveforms:
            self.instr.write("DATA:SOURCE %s" % ch)
            self.instr.write("DATA:ENC SRP")
            self.instr.write("DATA:START 1")
            self.instr.write("DATA:STOP %i" % samples)
            
            # Get scale factors for each channel
            y_scale = float(self.instr.query("WFMO:YMULT?"))
            y_zero = float(self.instr.query("WFMO:YZERO?"))
            y_offset = float(self.instr.query("WFMO:YOFF?"))
            y_units = str(self.instr.query("WFMO:YUNIT?"))
            self.logger.debug("Y Units: %s" % y_units)
            
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
    
    def getScreenshot(self, filename, format="PNG"):
        """
        Save a screenshot of the oscilloscope to a file.
        
        :param filename: File to save
        :type filename: str
        :param format: File format ('PNG', 'BMP' or 'TIFF')
        """
        if str(format).upper() in ['PNG', 'BMP', 'TIFF']:
            self.instr.write('SAVE:IMAG:FILEF %s' % format)
            self.instr.write('HARDCOPY START')
            raw_data = self.instr.read_raw()
            
            with open(filename, 'wb') as f:
                f.write(raw_data)
                
        else:
            raise ValueError("Invalid format")
            
        