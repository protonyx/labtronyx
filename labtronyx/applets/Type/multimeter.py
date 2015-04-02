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
                                  'BK_Precision.Multimeter.d_5492']
    }
    
    def test(self):
        return "1.0"
    
    def run(self):
        self.wm_title("Multimeter")
        
        self.instr = self.getInstrument()
        prop = self.instr.getProperties()
        
        # Driver info
        self.w_info = vw_info.vw_DriverInfo(self, self.instr)
        self.w_info.grid(row=0, column=0, columnspan=2)
        
        #=======================================================================
        # Configuration
        #=======================================================================
        # Mode
        self.f_conf = Tk.LabelFrame(self, text="Configuration")
        self.w_mode = vw_entry.vw_List(self.f_conf, 
                                       values=prop.get('validModes', []),
                                       get_cb=self.instr.getMode,
                                       set_cb=self.instr.setMode,
                                       label='Mode')
        self.w_mode.pack()
        
        # Range
        self.w_range = vw_entry.vw_Text(self.f_conf,
                                       get_cb=self.instr.getRange,
                                       set_cb=self.instr.setRange,
                                       label='Range')
        self.w_range.pack()
        
        # Trigger Source
        self.w_trig_source = vw_entry.vw_List(self.f_conf, 
                                       values=prop.get('validTriggerSources', []),
                                       get_cb=self.instr.getTriggerSource,
                                       set_cb=self.instr.setTriggerSource,
                                       label='Trigger Source')
        self.w_trig_source.pack()
        
        # Trigger
        self.w_trig = vw_state.vw_Trigger(self.f_conf,
                                          cb_func=self.instr.trigger,
                                          label="Bus Trigger",
                                          button_label="Trigger")
        self.w_trig.pack()
        
        self.f_conf.grid(row=1, column=0)
        #=======================================================================
        # Data
        #=======================================================================
        self.f_data = Tk.LabelFrame(self, text="Data")
        
        # Current Value
        self.w_data = vw_entry.vw_LCD(self.f_data, 
                                      get_cb=self.instr.getMeasurement,
                                      label="Measurement",
                                      update_interval=10000)
        self.w_data.grid(row=0, column=0)
        
        self.f_data.grid(row=2, column=0)
        
        #=======================================================================
        # Plot
        #=======================================================================
        self.w_graph = vw_plots.vw_Plot(self, title="Measurement")
        self.w_graph.addPlot(self.instr, method='getMeasurement')
        self.w_graph.grid(row=1, column=1, rowspan=2)
        
        
        