
#import multiprocessing
import Tkinter as Tk
from common.rpc import RpcClient

class v_Base(Tk.Toplevel):
    
    validVIDs = []
    validPIDs = []
    
    def __init__(self, master, parent, model):
        Tk.Toplevel.__init__(self, master)
        
        self.parent = parent
        self.model = model
            
    def run(self):
        raise NotImplementedError