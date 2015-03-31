from Base_Applet import Base_Applet

import Tkinter as Tk

from widgets import *

class multimeter(Base_Applet):
    
    info = {
        # View revision author
        'author':               'KKENNEDY',
        # View version
        'version':              '1.0',
        # Revision date of View version
        'date':                 '2015-03-11',    
        
        # List of compatible models
        'validDrivers':          ['Agilent.Multimeter.m_3441XA', 
                                  'BK_Precision.Multimeter.d_2831',
                                  'BK_Precision.Multimeter.d_5492',
                                  'Debug.m_debug']
    }
    
    def test(self):
        return "1.0"
    
    def run(self):
        self.wm_title("Multimeter")
        
        self.instr = self.getInstrument()
        
        # Driver info
        self.w_info = vw_info.vw_DriverInfo(self, self.instr)
        self.w_info.pack()
        
        self.w_data = vw_data.vw_DataLCD(self, get_cb=lambda: self.test())
        self.w_data.pack()
        
