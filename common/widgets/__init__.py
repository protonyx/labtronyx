import Tkinter as Tk

__all__ = ["entry", "plots", "state"]

class vw_Base(Tk.Frame):
    PIXELS_PER_X = 30
    PIXELS_PER_Y = 30
    
    def __init__(self, master, units_x=8, units_y=1):
        Tk.Frame.__init__(self, master, padx=2, pady=2)
        
        width = units_x * self.PIXELS_PER_X
        height = units_y * self.PIXELS_PER_Y
        
        self.config(width=width, height=height)
        self.pack_propagate(0)