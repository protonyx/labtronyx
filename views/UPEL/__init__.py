"""
UPEL View Helper Classes
"""

import Tkinter as Tk

class ICP_Sensor(Tk.Frame):
    def __init__(self, master, model, sensorNumber):
        Tk.Frame.__init__(self, master)
        
        self.model = model
        self.sensorNumber = sensorNumber
        
        self.name = 'test'#model.readRegisterValue(0x2120, sensorNumber)
        self.units = 'A'#model.readRegisterValue(0x2121, sensorNumber)
        
        sensorLabel = "%s:" % (self.name)
        
        Tk.Label(self, text=sensorLabel).grid(row=0, column=0)
        self.val = Tk.Label(self, text="???")
        self.val.grid(row=0, column=1)
        
    def update(self):
        val = 1#self.model.readRegisterValue(0x2122, self.sensorNumber)
        
class ICP_Register_Display(Tk.Frame):
    pass

class ICP_Register_Edit(Tk.Frame):
    pass