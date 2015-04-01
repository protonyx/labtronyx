from . import vw_Base

import Tkinter as Tk

#__all__ = ['vm_GetSetValue', 'vw_GetValue']

class vw_GetSetValue(vw_Base):
    """
    Widget to get and set values        
    """
    
    def __init__(self, master, get_cb, set_cb, **kwargs):
        """
        :param get_cb: Callback function for get
        :type get_gb: method
        :param set_cb: Callback function for set
        :type set_cb: method
        """
        vw_Base.__init__(self, master, 8, 1)
        
        self.get_cb = get_cb
        self.set_cb = set_cb
        
        # Label
        if 'label' in kwargs:
            label = kwargs.get('label')
            self.l_name = Tk.Label(self, width=10, text=label, anchor=Tk.W, justify=Tk.LEFT)
            self.l_name.pack(side=Tk.LEFT)
        
        # Set Button
        self.b_set = Tk.Button(self, text="Set", command=self.cb_set)
        self.b_set.pack(side=Tk.RIGHT)
        
        # Get Button
        if 'update_interval' not in kwargs:
            self.b_get = Tk.Button(self, text="Get", command=self.cb_get)
            self.b_get.pack(side=Tk.RIGHT, padx=3)
        
        # Units
        if 'units' in kwargs:
            units = kwargs.get('units')
            self.l_units = Tk.Label(self, width=2, text=units)
            self.l_units.pack(side=Tk.RIGHT)
        
        # Data
        self.val = Tk.StringVar()
        self.val.set("0")
        self.txt_data = Tk.Entry(self, width=6, textvariable=self.val)
        self.txt_data.pack(side=Tk.RIGHT)
        
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
            
class vw_GetValue(vw_Base):
    # Data Type?
    def __init__(self, master, get_cb, **kwargs):
        vw_Base.__init__(self, master, 8, 1)
        
        self.get_cb = get_cb
        
        # Label
        if 'label' in kwargs:
            label = kwargs.get('label')
            self.l_name = Tk.Label(self, width=10, font=("Purisa", 12), text=label, anchor=Tk.W, justify=Tk.LEFT)
            self.l_name.pack(side=Tk.LEFT)
            
        # Get Button
        self.b_set = Tk.Button(self, text="Get", command=self.cb_update)
        self.b_set.pack(side=Tk.RIGHT, padx=3)
        
        # Units
        if 'units' in kwargs:
            units = kwargs.get('units')
            self.l_units = Tk.Label(self, width=2, font=("Purisa", 12), text=units)
            self.l_units.pack(side=Tk.RIGHT)

        # Data
        self.val = Tk.StringVar()
        self.val.set("0")
        self.l_data = Tk.Label(self, width=6, font=("Purisa", 10), textvariable=self.val, relief=Tk.RIDGE)
        self.l_data.pack(side=Tk.RIGHT)
        
        self.update_interval = kwargs.get('update_interval', None)
        self._schedule_update()
        
    def get(self):
        return self.val.get()
            
    def cb_update(self):
        try:
            val = self.get_cb()
            val = "{:.2f}".format(val)
            
            self.val.set(val)
            
        except:
            self.l_data.config(bg="red")
            
class vw_List(vw_Base):
    def __init__(self, master, values, get_cb, set_cb, **kwargs):
        vw_Base.__init__(self, master, 12, 1)
        
        self.get_cb = get_cb
        self.set_cb = set_cb
        
        self.f_left = Tk.Frame(self, width=3*self.PIXELS_PER_X, height=1*self.PIXELS_PER_Y)
        self.f_middle = Tk.Frame(self, width=6*self.PIXELS_PER_X, height=1*self.PIXELS_PER_Y)
        self.f_right = Tk.Frame(self, width=3*self.PIXELS_PER_X, height=1*self.PIXELS_PER_Y)
        self.f_left.grid_propagate(0)
        self.f_middle.grid_propagate(0)
        self.f_right.grid_propagate(0)
        
        #=======================================================================
        # Left
        #=======================================================================
        # Label
        self.l_name = Tk.Label(self.f_left, width=10, 
                               text=kwargs.get('label', ''), 
                               anchor=Tk.W, justify=Tk.LEFT)
        self.l_name.grid(row=0, column=0, sticky=Tk.W)
        
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
        self.b_set = Tk.Button(self.f_right, text="Get", width=3, 
                               command=self.cb_get)
        self.b_set.grid(row=0, column=0, padx=3)
        
        # Set Button
        self.b_set = Tk.Button(self.f_right, text="Set", width=3, 
                               command=self.cb_set)
        self.b_set.grid(row=0, column=1, padx=3)
        
        #=======================================================================
        
        self.f_left.pack(side=Tk.LEFT)
        self.f_middle.pack(side=Tk.LEFT)
        self.f_right.pack(side=Tk.LEFT)
        
        self.update_interval = kwargs.get('update_interval', None)
        self._schedule_update()
        
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
        
    def get(self):
        return self.val.get()
            