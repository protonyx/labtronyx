
import views

import Tkinter as Tk

class v_UPEL(views.v_Base):
    
    validVIDs = ['UPEL']
    validPIDs = []
    
    def run(self):
        self.wm_title("UPEL ICP Test")
        
        #=======================================================================
        # Register Group
        #=======================================================================
        self.regGroup = Tk.LabelFrame(self, text="Registers", padx=10, pady=10)
        self.regGroup.pack(padx=10, pady=10)
        
        Tk.Label(self.regGroup, text="Address (Hex):").grid(row=0, column=0)
        self.reg_address = Tk.Entry(self.regGroup)
        self.reg_address.grid(row=0, column=1)
        
        Tk.Label(self.regGroup, text="Subindex (Hex):").grid(row=1,column=0)
        self.reg_subindex = Tk.Entry(self.regGroup)
        self.reg_subindex.grid(row=1, column=1)
        
        Tk.Label(self.regGroup, text="Value:").grid(row=2,column=0)
        self.val = Tk.StringVar()
        self.reg_value = Tk.Entry(self.regGroup, textvariable=self.val)
        self.reg_value.grid(row=2, column=1)
        
        Tk.Button(self.regGroup, text="Read", command=self.reg_read).grid(row=3,column=0)
        Tk.Button(self.regGroup, text="Write", command=self.reg_write).grid(row=3,column=1)
        
    def reg_read(self):
        address = int(self.reg_address.get(), 16)
        subindex = int(self.reg_subindex.get(), 16)
        
        value = self.model.readRegisterValue(address, subindex)
        
        self.val.set(value)
    
    def reg_write(self):
        address = int(self.reg_address.get(), 16)
        subindex = int(self.reg_subindex.get(), 16)
        value = self.val.get()
        
        self.model.writeRegisterValue(address, subindex, value)