
import views
import Tkinter as Tk

from . import ICP_Sensor

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
        # Sensor Frame
        numSensors = 2#self.model.readRegisterValue(0x2100, 0x1) # Number of Sensors
        self.sensorFrame = Tk.LabelFrame(self, text="Sensors", padx=5, pady=5)
        self.sensor = {}
        for x in range(1, numSensors+1):
            sens_obj = ICP_Sensor(self.sensorFrame, self.model, x)
            sens_obj.pack()
            self.sensor[x] = sens_obj
            
        self.sensorFrame.grid(row=0, column=0)
    
    def updateWindow(self):
        """
        Update window from BDPC Model
        """
    
class BDPC_Graph(Tk.Toplevel):
    
    def __init__(self):
        pass