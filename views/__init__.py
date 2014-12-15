
#import multiprocessing
import Tkinter as Tk
from common.rpc import RpcClient

class v_Base(Tk.Toplevel):
    
    validVIDs = []
    validPIDs = []
    
    def __init__(self, master, model):
        Tk.Toplevel.__init__(self, master, padx=5, pady=5)
        
        self.model = model
            
    def run(self):
        raise NotImplementedError
    
