import Tkinter as Tk
import tkMessageBox

class a_ConnectToHost(Tk.Toplevel):
    
    def __init__(self, master, cb_func):
        Tk.Toplevel.__init__(self, master)
        
        # Store reference to parent window callback function
        self.cb_func = cb_func
        
        self.wm_title('Connect to host...')
        Tk.Label(self, text='Connect to remote host').grid(row=0, column=0, columnspan=2)
        
        Tk.Label(self, text='Address or Hostname').grid(row=1, column=0)
        self.txt_address = Tk.Entry(self)
        self.txt_address.grid(row=1, column=1)
        
        Tk.Label(self, text='Port').grid(row=2, column=0)
        self.txt_port = Tk.Entry(self)
        self.txt_port.grid(row=2, column=1)
        
        Tk.Button(self, text='Cancel', command=lambda: self.cb_Cancel()).grid(row=3, column=0)
        Tk.Button(self, text='Connect', command=lambda: self.cb_Add()).grid(row=3, column=1)
        
        # Make this dialog modal
        self.focus_set()
        self.grab_set()
        
    def cb_Add(self):
        address = self.txt_address.get()
        port = self.txt_port.get()
        
        self.cb_func(address, port)
        
        # Close this window
        self.destroy()
        
    def cb_Cancel(self):
        self.destroy()
        
class a_AddResource(Tk.Toplevel):
    
    def __init__(self, master, mainWindow, controllers, cb_func):
        Tk.Toplevel.__init__(self, master)
        
        # Store reference to parent window callback function
        self.mainWindow = mainWindow
        
        self.cb_func = cb_func
        self.controller = Tk.StringVar(self)
        self.controller.set(controllers[0])
        
        self.wm_title('Add Resource')
        Tk.Label(self, text='Controller').grid(row=0, column=0)
        Tk.Label(self, text='Resource ID').grid(row=1, column=0)
        self.lst_controller = Tk.OptionMenu(self, self.controller, *controllers)
        self.lst_controller.grid(row=0, column=1, columnspan=2)
        self.txt_resID = Tk.Entry(self)
        self.txt_resID.grid(row=1, column=1, columnspan=2)
        Tk.Button(self, text='Cancel', command=lambda: self.cb_Cancel()).grid(row=2, column=1)
        Tk.Button(self, text='Connect', command=lambda: self.cb_Add()).grid(row=2, column=2)
            
        # Make this dialog modal
        #self.focus_set()
        #self.grab_set()
        
    def cb_Add(self):
        controller = self.controller.get()
        resID = self.txt_resID.get()
        
        self.cb_func(controller, resID)
        
        # Refresh treeview
        self.mainWindow.rebuildTreeview()
        
        # Close this window
        self.destroy()
        
    def cb_Cancel(self):
        self.destroy()
        
class a_AppletSelector(Tk.Toplevel):
    
    def __init__(self, master, applets, cb_func):
        Tk.Toplevel.__init__(self, master, padx=2, pady=2)
        
        # Store reference to parent window callback function
        self.cb_func = cb_func
        self.applet = Tk.StringVar(self)
        self.applet.set(applets[0])
        
        self.wm_title('Load an Applet...')
        Tk.Label(self, text='Multiple applets found, select one to load:').grid(row=0, column=0, columnspan=2)
        self.lst_view = Tk.OptionMenu(self, self.applet, *applets).grid(row=1, column=0, columnspan=2)
        Tk.Button(self, text='Cancel', command=lambda: self.cb_Cancel()).grid(row=2, column=0)
        Tk.Button(self, text='Launch', command=lambda: self.cb_Load()).grid(row=2, column=1)
        
        # Make this dialog modal
        self.focus_set()
        self.grab_set()
        
    def cb_Load(self):
        applet = self.applet.get()
        
        self.cb_func(applet)
        
        # Close this window
        self.destroy()
        
    def cb_Cancel(self):
        self.destroy()
        
class a_LoadDriver(Tk.Toplevel):
    
    instructions = "A driver could not automatically be loaded for this instrument, please provide the vendor and model to load the proper driver."
    
    def __init__(self, master, ICF, uuid):
        Tk.Toplevel.__init__(self, master, padx=2, pady=2)
        
        self.ICF = ICF
        self.uuid = uuid
        
        self.res = self.ICF.getInstrument(self.uuid)
        self.resInfo = self.ICF.getResources().get(self.uuid)
        self.resType = self.resInfo.get('resourceType')
        self.address = self.resInfo.get('address')
        
        # Find valid drivers for this resource type
        allDrivers = self.ICF.getDrivers(self.address)
        self.validDrivers = {}
        for driverModule, driverInfo in allDrivers.items():
            if self.resType in driverInfo.get('validResourceTypes', []):
                self.validDrivers[driverModule] = driverInfo
        
        self.wm_title('Load a Driver...')
        self.lbl_instructions = Tk.Label(self, text=self.instructions,
                                         width=50,
                                         wraplength=350)
        self.lbl_instructions.grid(row=0, column=0, columnspan=2)

        # Vendors
        self.frame_vendors = Tk.Frame(self)
        self.lbl_vendors = Tk.Label(self.frame_vendors, 
                                    text="Vendors")
        self.lbl_vendors.pack(side=Tk.TOP)
        self.var_vendors = Tk.StringVar()
        self.lst_vendor = Tk.Listbox(self.frame_vendors, 
                                     listvariable=self.var_vendors,
                                     activestyle=Tk.NONE)
        self.lst_vendor.pack(side=Tk.TOP, fill=Tk.BOTH)
        self.frame_vendors.grid(row=1, column=0, 
                                sticky=Tk.N+Tk.E+Tk.S+Tk.W,
                                padx=5, pady=5)

        # Models
        self.frame_models = Tk.Frame(self)
        self.lbl_models = Tk.Label(self.frame_models, 
                                   text="Models")
        self.lbl_models.pack(side=Tk.TOP)
        self.var_models = Tk.StringVar()
        self.lst_model = Tk.Listbox(self.frame_models, 
                                    listvariable=self.var_models,
                                    activestyle=Tk.NONE)
        self.lst_model.pack(side=Tk.TOP, fill=Tk.BOTH)
        self.frame_models.grid(row=1, column=1, 
                               sticky=Tk.N+Tk.E+Tk.S+Tk.W,
                               padx=5, pady=5)

        # Buttons
        self.frame_buttons = Tk.Frame(self)
        self.btn_cancel = Tk.Button(self.frame_buttons, text='Cancel',
                                    command=lambda: self.cb_Cancel()
                                    )
        self.btn_cancel.grid(row=0, column=0)
        self.btn_ok = Tk.Button(self.frame_buttons, text='Load',
                                command=lambda: self.cb_Load()
                                )
        self.btn_ok.grid(row=0, column=1)
        self.frame_buttons.grid(row=2, column=0, columnspan=2,
                                padx=5, pady=5)
        
        # Event Bindings
        self.lst_vendor.bind('<ButtonRelease-1>', self.e_VendorClick)
        self.lst_model.bind('<ButtonRelease-1>', self.e_ModelClick)
        
        self.populateVendors()
        
        # Make this dialog modal
        self.focus_set()
        self.grab_set()
        
    def populateVendors(self):
        # Populate Vendor list
        vendors = []
        for driverInfo in self.validDrivers.values():
            deviceVendor = driverInfo.get('deviceVendor')
            if deviceVendor is not None and deviceVendor not in vendors:
                vendors.append(str(deviceVendor))
        vendors.sort()
        self.lst_vendor.insert(Tk.END, *vendors)
        self.selectedVendor = None
        self.selectedModel = None
        
    def e_VendorClick(self, event):
        self.selectedVendor = self.lst_vendor.curselection()[0]
        self.selectedVendor = self.lst_vendor.get(self.selectedVendor)
        self.lst_model.delete(0, Tk.END)
    
        filtered_models = []
        for modelInfo in self.validDrivers.values():
            modelVendor = modelInfo.get('deviceVendor')
            if self.selectedVendor == modelVendor:
                deviceModel = modelInfo.get('deviceModel')
                filtered_models.extend(deviceModel)
        filtered_models.sort()
        self.lst_model.insert(Tk.END, *filtered_models)
        
    def e_ModelClick(self, event):
        self.selectedModel = self.lst_model.curselection()[0]
        self.selectedModel = self.lst_model.get(self.selectedModel)
        
    def cb_Load(self):
        if self.selectedModel is not None and self.selectedVendor is not None:
            # Load the selected model
            for modelModule, modelInfo in self.validDrivers.items():
                if self.selectedVendor == modelInfo.get('deviceVendor') and \
                    self.selectedModel in modelInfo.get('deviceModel'):
                    
                    if not self.res.loadDriver(modelModule):
                        tkMessageBox.showwarning('Unable to load driver', 'An error occured while loading the driver')
                        
                    self.ICF.refreshResources()
                    self.ICF.refreshInstrument(self.uuid)
            
                    # Close this window
                    self.destroy()
        
        else:
            tkMessageBox.showerror('Load Driver', 'Please select a driver to load')
        
    def cb_Cancel(self):
        self.destroy()
    