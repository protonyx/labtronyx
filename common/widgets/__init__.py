import Tkinter as Tk

__all__ = ["vw_entry", "vw_info", "vw_plots", "vw_state"]

class vw_Base(Tk.Frame):
    PIXELS_PER_X = 30
    PIXELS_PER_Y = 30
    
    def __init__(self, master, units_x=8, units_y=1):
        Tk.Frame.__init__(self, master, padx=2, pady=2)
        
        width = units_x * self.PIXELS_PER_X
        height = units_y * self.PIXELS_PER_Y
        
        self.config(width=width, height=height)
        self.pack_propagate(0)
        
        self.update_interval = None
        
    def _schedule_update(self):
        if self.update_interval is not None:
            self.after(self.update_interval, self.e_update)
        else:
            self.after(100, self.cb_update)
            
    def e_update(self):
        """
        Event to handle self-updating
        """
        self.cb_update()
        
        if self.update_interval is not None:
            self._schedule_update()
            
    def cb_update(self):
        raise NotImplementedError