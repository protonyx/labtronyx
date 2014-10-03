
import views
import Tkinter as Tk

from . import *

class v_BDPC(views.v_Base):
    """
    BDPC View. Collects and displays the following information:
    
    BDPC Parameters:
    
        * Phase Shift from SYNC
        * Operation Mode (Switching On/Off)
    
    Main Controller:
    
        * Controller Gain
        * Power Command
        * Conversion Ratio
        * Phi AB, AD, DC
    
    Controller Programmable Parameters:
    
        * Dead Time (Td)
        * Controller Gain
        * Open Loop Power Command
        * MMC Params?
        
    Auxiliary Leg Controllers:
    
        * Angle Command (ACMD or Phi')
        * Desired ZVS current
        * Measured ZVS current
        * Minimum Angle Command
        
    Aux Controller Programmable Parameters:
    
        * Dead Time (Tda)
        * Open Loop Angle Command
    """
    
    validVIDs = ['UPEL']
    validPIDs = []
    
    def run(self):
        #=======================================================================
        # Parameters
        #=======================================================================
        self.frame_param = Tk.LabelFrame(self, text="Operation", padx=5, pady=5)
        
        self.frame_param.grid(row=0, column=0, columnspan=3)
        
        # Primary
        self.frame_primary = Tk.LabelFrame(self, text="Primary", padx=5, pady=5)
        self.pri_sensor_voltage = ICP_Sensor(self.frame_primary, self.model, 1)
        self.pri_sensor_voltage.pack()
        self.pri_sensor_current = ICP_Sensor(self.frame_primary, self.model, 3)
        self.pri_sensor_current.pack()
        self.pri_power = ICP_Value_Read(self.frame_primary, self.model, 
                                        label="Input Power", units="W", read_cb=self.model.getPrimaryPower)
        self.pri_power.pack()
        self.frame_primary.grid(row=1, column=0)
        
        # Picture Frame
        
        # Secondary
        self.frame_secondary = Tk.LabelFrame(self, text="Secondary", padx=5, pady=5)
        self.sec_sensor_voltage = ICP_Sensor(self.frame_secondary, self.model, 2)
        self.sec_sensor_voltage.pack()
        self.sec_sensor_current = ICP_Sensor(self.frame_secondary, self.model, 4)
        self.sec_sensor_current.pack()
        self.sec_power = ICP_Value_Read(self.frame_secondary, self.model, 
                                        label="Output Power", units="W", read_cb=self.model.getSecondaryPower)
        self.sec_power.pack()
        self.frame_secondary.grid(row=1, column=2)
    
    def updateWindow(self):
        """
        Update window from BDPC Model
        """
    
class BDPC_Graph(Tk.Toplevel):
    
    def __init__(self):
        pass