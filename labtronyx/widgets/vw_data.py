from . import vw_Base

import Tkinter as Tk

class vw_DataLCD(vw_Base):
    
    def __init__(self, master, get_cb, **kwargs):
        """
        :param get_cb: Callback function for get
        :type get_gb: method
        :param units: Units
        :type units: str
        """
        vw_Base.__init__(self, master)
        
        self.get_cb = get_cb
        
        self.data = Tk.StringVar(self)
        self.units = Tk.StringVar(self)
        self.units.set(kwargs.get('units', ''))
        
        self.f_data = Tk.Frame(self, bg='black', padx=5, pady=5)
        self.l_data = Tk.Label(self.f_data, textvariable=self.data,
                               font=('Courier New', '12'),
                               bg='black', fg='green')
        self.l_data.pack(side=Tk.LEFT)
        self.l_units = Tk.Label(self.f_data, textvariable=self.units,
                                bg='black', fg='green')
        self.l_units.pack(side=Tk.LEFT)
        self.f_data.pack()
    
        self.update_interval = kwargs.get('update_interval', None)
        self._schedule_update()
        
    def cb_update(self):
        data = self.get_cb()
        
        self.data.set(data)