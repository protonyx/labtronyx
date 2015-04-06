from . import vw_Base

import Tkinter as Tk

class vw_DriverInfo(vw_Base):
    """
    Driver info widget
    
    Host
    * Address/Hostname
    * Controller
    
    Resource
    * Resource type
    * Resource ID
    * Driver name
    * Status
    
    Device
    * Device vendor
    * Device model
    * Device Serial
    * Device Firmware
    """
    
    def __init__(self, master, resource):
        vw_Base.__init__(self, master, 8, 1)
        self.resource = resource
        
        #=======================================================================
        # Resource
        #=======================================================================
        self.l_type = Tk.StringVar(self)
        self.l_id = Tk.StringVar(self)
        self.l_driver = Tk.StringVar(self)
        self.l_vendor = Tk.StringVar(self)
        self.l_model = Tk.StringVar(self)
        self.l_serial = Tk.StringVar(self)
        self.l_firmware = Tk.StringVar(self)
        
        self.f_resource = Tk.Frame(self)
        Tk.Label(self.f_resource, text="Type", width=10, 
                 anchor=Tk.W, justify=Tk.LEFT).grid(row=0, column=0)
        Tk.Label(self.f_resource, textvariable=self.l_type).grid(row=0, column=1, 
                                                                   sticky=Tk.W,
                                                                   padx=5)
                 
        Tk.Label(self.f_resource, text="Identifier", width=10, 
                 anchor=Tk.W, justify=Tk.LEFT).grid(row=1, column=0)
        Tk.Label(self.f_resource, textvariable=self.l_id).grid(row=1, column=1, 
                                                                   sticky=Tk.W,
                                                                   padx=5)
                 
        Tk.Label(self.f_resource, text="Driver", width=10, 
                 anchor=Tk.W, justify=Tk.LEFT).grid(row=2, column=0)
        Tk.Label(self.f_resource, textvariable=self.l_driver).grid(row=2, column=1, 
                                                                   sticky=Tk.W,
                                                                   padx=5)
        self.f_resource.grid(row=0, column=0)
        
        self.f_device = Tk.Frame(self)
        Tk.Label(self.f_device, text="Vendor", width=15, 
                 anchor=Tk.W, justify=Tk.LEFT).grid(row=0, column=0)
        Tk.Label(self.f_device, textvariable=self.l_vendor).grid(row=0, column=1, 
                                                                   sticky=Tk.W,
                                                                   padx=5)
                 
        Tk.Label(self.f_device, text="Model", width=15, 
                 anchor=Tk.W, justify=Tk.LEFT).grid(row=1, column=0)
        Tk.Label(self.f_device, textvariable=self.l_model).grid(row=1, column=1, 
                                                                   sticky=Tk.W,
                                                                   padx=5)
                 
        Tk.Label(self.f_device, text="Serial Number", width=15, 
                 anchor=Tk.W, justify=Tk.LEFT).grid(row=2, column=0)
        Tk.Label(self.f_device, textvariable=self.l_serial).grid(row=2, column=1, 
                                                                   sticky=Tk.W,
                                                                   padx=5)
        self.f_device.grid(row=0, column=1, padx=10)
        
        self.cb_update()
        
    def cb_update(self):
        prop = self.resource.getProperties()
        
        self.l_type.set(prop.get("resourceType", ''))
        self.l_id.set(prop.get("resourceID", ''))
        self.l_driver.set(prop.get("driver", ''))
        
        self.l_vendor.set(prop.get("deviceVendor", ''))
        self.l_model.set(prop.get("deviceModel", ''))
        self.l_serial.set(prop.get("deviceSerial", ''))
        
        