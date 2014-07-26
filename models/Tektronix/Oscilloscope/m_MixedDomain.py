# Models:
# MDO 3XXX, 4XXX
from m_DigitalPhosphor import m_DigitalPhosphor

class m_MixedDomain(m_DigitalPhosphor):
        
    validPIDs = [ # MDO3XXX Series
                    
                    # MDO4XXX Series
                    
                    ]
    
    def onLoad(self):
        m_DigitalPhosphor.onLoad(self)
        
        self.logger.debug("Loaded Tektronix Mixed Domain Oscilloscope Model")