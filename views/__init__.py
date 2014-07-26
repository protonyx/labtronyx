
import multiprocessing
from common.rpc import RpcClient

class v_Base(multiprocessing.Process):
    
    def __init__(self, **kwargs):
        multiprocessing.Process.__init__(self)
        
        if 'port' in kwargs:
            self.port = kwargs['port']
        else:
            self.port = None
        
        if 'address' in kwargs:
            self.address = kwargs['address']
        else:
            # Assume localhost
            self.address = '127.0.0.1'
            
    def start(self):
        multiprocessing.Process.start(self)
        
        # Instantiate an RPC Client
        if self.port != None:
            self.target = RpcClient(port=self.port) 

    def run(self):
        raise NotImplementedError
    
    def stop(self):
        raise NotImplementedError