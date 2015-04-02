from . import vw_Base

import Tkinter as Tk

#__all__ = ['vm_GetSetValue', 'vw_GetValue']

class vw_Base_Entry(vw_Base):
    def __init__(self, master, **kwargs):
        vw_Base.__init__(self, master, 12, 1)
        
        self.f_left = Tk.Frame(self)
        self.f_middle = Tk.Frame(self)
        self.f_right = Tk.Frame(self)
        
        #=======================================================================
        # Left
        #=======================================================================
        # Label
        self.l_name = Tk.Label(self.f_left, width=15, 
                               text=kwargs.get('label', ''), 
                               fg='black',
                               anchor=Tk.W, justify=Tk.LEFT)
        self.l_name.pack()
    
        self.f_left.pack(side=Tk.LEFT)
        self.f_middle.pack(side=Tk.LEFT)
        self.f_right.pack(side=Tk.RIGHT)

class vw_Text(vw_Base_Entry):
    """
    Widget to get and set values        
    """
    
    def __init__(self, master, get_cb=None, set_cb=None, **kwargs):
        """
        :param get_cb: Callback function for get
        :type get_gb: method
        :param set_cb: Callback function for set
        :type set_cb: method
        """
        vw_Base_Entry.__init__(self, master, **kwargs)
        
        self.get_cb = get_cb
        self.set_cb = set_cb
        
        #=======================================================================
        # Middle
        #=======================================================================
        # Data
        self.val = Tk.StringVar()
        self.l_data = Tk.Entry(self.f_middle, width=6, textvariable=self.val)
        self.l_data.grid(row=0, column=0, sticky=Tk.W)
        
        # Units
        self.l_units = Tk.Label(self.f_middle, width=2, text=kwargs.get('units', ''))
        self.l_units.grid(row=0, column=1)
            
        #=======================================================================
        # Right
        #=======================================================================
        # Get Button
        self.b_get = Tk.Button(self.f_right, text="Get", width=3, 
                               command=self.cb_get)
        if self.get_cb is None:
            self.b_get.config(state=Tk.DISABLED)
        self.b_get.grid(row=0, column=0, padx=3)
        
        # Set Button
        self.b_set = Tk.Button(self.f_right, text="Set", width=3, 
                               command=self.cb_set)
        if self.set_cb is None:
            self.b_set.config(state=Tk.DISABLED)
        self.b_set.grid(row=0, column=1, padx=3)
        
        #=======================================================================

        self.update_interval = kwargs.get('update_interval', None)
        self._schedule_update()
        
    def get(self):
        # Get the value in the entry
        return self.val.get()
    
    def set(self, val):
        # Set the value in the entry
        self.val.set(val)
        # Also trigger the callback
        cb_set()
    
    def cb_update(self):
        val = self.get_cb()
        self.val.set(val)
        
    def cb_get(self):
        try:
            val = self.get_cb()
            
            self.val.set(val)
            
        except:
            self.txt_data.config(bg='red')
        
    def cb_set(self):
        try:
            self.set_cb(self.val.get())
            
        except:
            self.txt_data.config(bg='red')
            
class vw_List(vw_Base_Entry):
    def __init__(self, master, values, get_cb, set_cb, **kwargs):
        vw_Base_Entry.__init__(self, master, **kwargs)
        
        self.get_cb = get_cb
        self.set_cb = set_cb
        
        #=======================================================================
        # Middle
        #=======================================================================
        # Data
        self.val = Tk.StringVar()
        self.l_data = Tk.OptionMenu(self.f_middle, self.val, *values)
        self.l_data.grid(row=0, column=0, sticky=Tk.W)
            
        #=======================================================================
        # Right
        #=======================================================================
        # Get Button
        self.b_get = Tk.Button(self.f_right, text="Get", width=3, 
                               command=self.cb_get)
        if self.get_cb is None:
            self.b_get.config(state=Tk.DISABLED)
        self.b_get.grid(row=0, column=0, padx=3)
        
        # Set Button
        self.b_set = Tk.Button(self.f_right, text="Set", width=3, 
                               command=self.cb_set)
        if self.set_cb is None:
            self.b_set.config(state=Tk.DISABLED)
        self.b_set.grid(row=0, column=1, padx=3)
        
        #=======================================================================
        
        self.update_interval = kwargs.get('update_interval', None)
        self._schedule_update()
        
    def get(self):
        return self.val.get()
    
    def set(self, newval):
        self.val.set(newval)
        self.cb_set()
        
    def cb_update(self):
        self.cb_get()
        
    def cb_get(self):
        try:
            val = self.get_cb()
            
            self.val.set(val)
            
        except:
            pass
        
    def cb_set(self):
        try:
            self.set_cb(self.val.get())
            
        except:
            pass
            
class vw_LCD(vw_Base_Entry):
    
    def __init__(self, master, get_cb, **kwargs):
        """
        :param get_cb: Callback function for get
        :type get_gb: method
        :param units: Units
        :type units: str
        """
        vw_Base_Entry.__init__(self, master, **kwargs)
        
        self.get_cb = get_cb
        
        self.data = Tk.StringVar(self)
        self.units = Tk.StringVar(self)
        self.units.set(kwargs.get('units', ''))
        
        #=======================================================================
        # Middle
        #=======================================================================
        # Data
        self.f_data = Tk.Frame(self.f_middle, bg='black', padx=5, pady=5)
        self.l_data = Tk.Label(self.f_data, textvariable=self.data,
                               font=('Courier New', '14'),
                               width=15,
                               bg='black', fg='green')
        self.l_data.pack(side=Tk.LEFT)
        self.l_units = Tk.Label(self.f_data, textvariable=self.units,
                                bg='black', fg='green')
        self.l_units.pack(side=Tk.LEFT)
        self.f_data.pack()
        
        #=======================================================================
    
        self.update_interval = kwargs.get('update_interval', None)
        self._schedule_update()
        
    def setUnits(self, units):
        self.units.set(units)
        
    def cb_update(self):
        data = self.get_cb()
        
        self.data.set(data)