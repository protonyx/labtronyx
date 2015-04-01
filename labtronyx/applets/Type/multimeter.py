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
        self.w_info.grid(row=0, column=0, columnspan=2)
        
        #=======================================================================
        # Configuration
        #=======================================================================
        # Mode
        self.f_conf = Tk.LabelFrame(self, text="Configuration")
        self.w_mode = vw_entry.vw_List(self.f_conf, values=self.instr.getModes(),
                                       get_cb=self.instr.getMode,
                                       set_cb=self.instr.setMode,
                                       label='Mode')
        self.w_mode.pack()
        
        # Range
        
        # Trigger
        
        self.f_conf.grid(row=1, column=0)
        #=======================================================================
        # Data
        #=======================================================================
        self.f_data = Tk.Frame(self)
        
        self.w_data = vw_data.vw_DataLCD(self, get_cb=lambda: self.instr.getMeasurement())
        self.w_data.grid(row=1, column=1)
        
        # Plot
        
        self.f_data.grid(row=1, column=1)
        