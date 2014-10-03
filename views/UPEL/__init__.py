"""
UPEL View Helper Classes
"""

import Tkinter as Tk

class ICP_Widget(Tk.Frame):
    def __init__(self, master, model):
        Tk.Frame.__init__(self, master, padx=2, pady=2)

class ICP_Value_Read(ICP_Widget):
    # Data Type?
    def __init__(self, master, model, label, units, read_cb):
        ICP_Widget.__init__(self, master, model)
        
        self.read_cb = read_cb
        
        # Label
        self.l_name = Tk.Label(self, width=15, font=("Purisa", 12), text=label, anchor=Tk.W, justify=Tk.LEFT)
        self.l_name.pack(side=Tk.LEFT)

        # Data
        self.val = Tk.StringVar()
        self.val.set("0")
        self.l_data = Tk.Label(self, font=("Purisa", 12), textvariable=self.val, relief=Tk.RIDGE)
        self.l_data.pack(side=Tk.LEFT)
        
        # Units
        self.l_units = Tk.Label(self, font=("Purisa", 12), text=units)
        self.l_units.pack(side=Tk.LEFT)
        
    def update(self):
        val = self.read_cb()
           
        self.val.set(val)

class ICP_Value_ReadWrite(ICP_Widget):
    # Data Type?
    pass

class ICP_Value_Toggle(ICP_Widget):
    # Register Address
    # Bit Number
    pass

class ICP_Sensor(ICP_Value_Read):
    """
    ICP Sensor Class is a specific type of register for
    sensors.
    
    TODO: Add Calibration editor
    """
    
    def __init__(self, master, model, sensorNumber):
        self.model = model
        self.sensorNumber = sensorNumber
        
        sensor = self.model.getSensorType(sensorNumber)
        
        name = sensor.get('description', 'Sensor')
        units = sensor.get('units', '')
        
        ICP_Value_Read.__init__(self, master, model, label=name, units=units, 
                                      read_cb=lambda: self.model.getSensorValue(sensorNumber))
        
