
import application.views as views

import Tkinter as Tk

class v_UPEL(views.v_Base):
    
    info = {
        # View revision author
        'author':               'KKENNEDY',
        # View version
        'version':              '1.0',
        # Revision date of View version
        'date':                 '2015-02-11',  
        # Description
        'description':          'Generic view for UPEL ICP Resources',  
            
        # List of compatible resource types
        'validResourceTypes':   ['UPEL']
    }
    
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
        
        Tk.Label(self.regGroup, text="Data Type:").grid(row=3,column=0)
        self.var_type = Tk.StringVar()
        self.validTypes = ['string', 'int8', 'int16', 'int32', 'int64', 'float', 'double']
        self.lst_type = Tk.OptionMenu(self.regGroup, self.var_type, *self.validTypes)
        self.lst_type.grid(row=3, column=1)
        
        Tk.Button(self.regGroup, text="Read", command=self.reg_read).grid(row=4,column=0)
        Tk.Button(self.regGroup, text="Write", command=self.reg_write).grid(row=4,column=1)
        
    def reg_read(self):
        address = int(self.reg_address.get(), 16)
        subindex = int(self.reg_subindex.get(), 16)
        data_type = self.var_type.get()
        if data_type == 'string':
            data_type = ''
        
        value = self.model.readRegister(address, subindex, data_type)
        
        self.val.set(value)
    
    def reg_write(self):
        address = int(self.reg_address.get(), 16)
        subindex = int(self.reg_subindex.get(), 16)
        data_type = self.var_type.get()
        if data_type == 'string':
            data_type = ''
            
        value = self.val.get()
        
        self.model.writeRegister(address, subindex, data_type, value)