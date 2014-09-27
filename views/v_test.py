import views
import common
#from common.jsonrpc import *
from common.rpc import *

import Tkinter as Tk

class v_test(views.v_Base):
    
    validVIDs = ['Test']
    validPIDs = ['12345']
        
    def run(self):
        self.wm_title("RPC Test")
        
        # GUI Elements
        # Labels
        Tk.Label(self, text='Method').grid(row=0, column=1)
        Tk.Label(self, text='Params').grid(row=1, column=1)
        Tk.Label(self, text='Id').grid(row=2, column=1)
        
        # Text fields
        self.txtMethod = Tk.Entry(self)
        self.txtMethod.grid(row=0,column=2)
        self.txtParams = Tk.Entry(self)
        self.txtParams.grid(row=1,column=2)
        self.txtId = Tk.Entry(self)
        self.txtId.grid(row=2,column=2)
        
        # Listbox frame
        self.frameMethods = Tk.Frame(self)
        self.frameMethods.grid(row=0,column=0,rowspan=3)
        scrollbar = Tk.Scrollbar(self.frameMethods, orient=Tk.VERTICAL)
        self.methodList = Tk.Listbox(self.frameMethods, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.methodList.yview)
        scrollbar.pack(side=Tk.RIGHT, fill=Tk.Y)
        self.methodList.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=1)
        
        # Buttons
        self.btnSend = Tk.Button(self, text="Send", command=self.cb_Send)
        self.btnSend.grid(row=3,column=2)
        
        for proc in self.model.methods:
            self.methodList.insert(Tk.END, proc)
        
    def cb_Send(self):
        method = str(self.txtMethod.get())
        if hasattr(self.model, method):
            ret = getattr(self.model, method)()
        else:
            ret = 'Method not found'
            
        import ctypes  # An included library with Python install.
        def Mbox(title, text, style):
            ctypes.windll.user32.MessageBoxA(0, text, title, style)
        Mbox('Your title', str(ret), 1)
        
        