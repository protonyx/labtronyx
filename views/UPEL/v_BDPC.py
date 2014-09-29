
import views
import Tkinter as Tk

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
        pass
    
class BDPC_Graph(Tk.Toplevel):
    
    def __init__(self):
        pass