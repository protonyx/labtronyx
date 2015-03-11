# Models:
# MSO 2XXX, 3XXX, 4XXX, 5XXX
from m_Oscilloscope import m_Oscilloscope

class m_MixedSignal(m_Oscilloscope):
    
    info = {
        # Model revision author
        'author':               'KKENNEDY',
        # Model version
        'version':              '1.0',
        # Revision date of Model version
        'date':                 '2015-03-11',
        # Device Manufacturer
        'deviceVendor':         'Tektronix',
        # List of compatible device models
        'deviceModel':          [# MSO2XXX Series
                    
                                # MSO3XXX Series
                    
                                # MSO4XXX Series
                    
                                # MSO5XXX Series
                                "MSO5034", "MSO5034B", "MSO5054", "MSO5054B", 
                                "MSO5104", "MSO5104B", "MSO5204", "MSO5204B"
                                # MSO7XXXX Series
                                "MSO70404C", "MSO70604C", "MSO70804C", 
                                "MSO71254C", "MSO71604C", "MSO72004C", 
                                "MSO72304DX", "MSO72504DX", "MSO73304DX"],
            
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
        'VISA_compatibleModels':        ["MSO5034", "MSO5034B", "MSO5054", 
                                         "MSO5054B", "MSO5104", "MSO5104B", 
                                         "MSO5204", "MSO5204B", "MSO70404C", 
                                         "MSO70604C", "MSO70804C", "MSO71254C", 
                                         "MSO71604C", "MSO72004C", "MSO72304DX", 
                                         "MSO72504DX", "MSO73304DX"]
    }

    def _onLoad(self):
        m_Oscilloscope._onLoad(self)
        
        self.logger.debug("Loaded Tektronix Mixed Signal Oscilloscope Model")