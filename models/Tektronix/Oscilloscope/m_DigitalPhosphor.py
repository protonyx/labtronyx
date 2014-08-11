# Models:
# DPO 2XXX, 3XXX, 4XXX, 5XXX
#from . import Oscilloscope
from . import m_OscilloscopeBase

class m_DigitalPhosphor(m_OscilloscopeBase):
    
    validPIDs = [ # DPO2XXX Series
                    
                    # DPO3XXX Series
                    
                    # DPO4XXX Series
                    
                    # DPO5XXX Series
                    "DPO5054", "DPO5054B", "DPO5104", "DPO5104B", "DPO5204", "DPO5204B", "DPO5034", "DPO5034B",
                    # DPO7XXX Series
                    "DPO7054C", "DPO7104C", "DPO7254C", "DPO7354C",
                    # DPO7XXXX Series
                    "DPO70404C", "DPO70604C", "DPO70804C", "DPO71254C", "DPO71604C", "DPO72004C", 
                    "DPO72304DX", "DPO72504DX", "DPO73304DX"
                    ]
        
    def _onLoad(self):
        m_OscilloscopeBase._onLoad(self)
        
        self.logger.debug("Loaded Tektronix Digital Phosphor Oscilloscope Model")