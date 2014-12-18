import threading
from . import m_BDPC_Serial_Base

class m_BDPC_BR32(m_BDPC_Serial_Base):
    """
    
    """
    
    def getProperties(self):
        prop = m_BDPC.getProperties(self)
        
        prop['deviceVendor'] = 'UPEL'
        prop['deviceModel'] = 'BDPC 32kW'
        
        return prop
    
