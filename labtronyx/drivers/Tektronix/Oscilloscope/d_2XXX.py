from Base_Driver import Base_Driver

import time
import struct
import base64
import csv
import sys

import numpy

class d_2XXX(Base_Driver):
    
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
        'deviceModel':          [
                                "DPO2024"],
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
        'VISA_compatibleModels':        ["DPO2024"]
    }
    
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
    
    def getWaveform(self):
        """
        Get the waveform data from the oscilloscope
        """
        pass
    
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
            
        