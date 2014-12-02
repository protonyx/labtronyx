"""
Test
"""

import common
import common.rpc

import sys
import importlib
import logging

import views

class m_Base(common.rpc.RpcBase, common.IC_Common):
    
    deviceType = 'Generic'
    view = None
    
    # Model Lookup
    validControllers = []
    validVIDs = []
    validPIDs = []
    
    _collector_thread = None
    _collector_methods = {}
    _collector_last_sample = {}
    
    def __init__(self, uuid, controller, resID, VID, PID, **kwargs):
        common.rpc.RpcBase.__init__(self)
        common.IC_Common.__init__(self, **kwargs)
        
        self.uuid = uuid
        self.controller = controller
        self.resID = resID
        self.VID = VID
        self.PID = PID
        
        # Check for logger
        self.logger = kwargs.get('Logger', logging)
        
    #===========================================================================
    # Collector Functionality
    #===========================================================================
    
    def __collector_thread(self):
        """
        Asynchronous thread that automatically polls methods that are marked
        for collection
        """
        next_sample = {}
        
        while (len(self.acc_config) > 0):
            for reg, acc_config in self.acc_config.items():
                # Check if it is time to get a new sample
                if time.time() > next_sample.get(reg, 0.0):
                    address, subindex = reg
                    _, sample_time, data_type = acc_config
                    
                    # Queue a register read, the ICP thread will handle the data when it comes back
                    self.register_read_queue(address, subindex, data_type)
                    
                    # Increment the next sample time
                    next_sample[reg] = next_sample.get(reg, time.time()) + sample_time
                    
            # TODO: Calculate the time to the next sample and sleep until then
        
        # Clear reference to this thread before exiting
        self._collector_thread = None
        
    def startCollector(self, method, interval, depth):
        """
        Starts a Collector thread to retrieve data at a regular interval.
        
        :param method: Name of the Model method to invoke
        :type method: str
        :param interval: Interval in milliseconds between method invokations
        :type interval: int
        :param depth: Number of samples to keep
        :type depth: int
        :returns: Boolean, True if successful, False otherwise.
        """
        key = (address, subindex)
        self.reg_cache[key] = ''
        self.acc_config[key] = (depth, sample_time, data_type)
        
        # Create a new accumulator object
        self.accumulators[key] = UPEL_ICP_Accumulator(depth, data_type)
        
        # Start the accumulator thread
        if self.acc_thread is None:
            self.acc_thread = threading.Thread(target=self.__accumulator_thread)
            self.acc_thread.start()
    
    def stopCollector(self, method):
        pass
    
    
            
    #===========================================================================
    # Virtual Functions
    #===========================================================================
        
    def _onLoad(self):
        """
        Called shortly after a Model is instantiated. Since Models can be run
        in a new thread, all member attributes in __init__ must be pickleable.
        If there are attributes that cannot be pickled, load them here.
        """
        raise NotImplementedError
    
    def _onUnload(self):
        """
        Called when a Model is unloaded by the InstrumentManager. After this
        function is called, all reference will be nulled, and the object will
        be marked for Garbage Collection. This function should ensure that no
        object references are orphaned.
        """
        raise NotImplementedError
    
    #===========================================================================
    # Inherited Functions
    #===========================================================================
    
    def getModelName(self):
        """
        Returns the Model class name
        
        :returns: str
        """
        return self.__class__.__name__
    
    def getUUID(self):
        """
        Returns the Resource UUID that is provided to the Model
        
        :returns: str
        """
        return self.uuid
    
    def getControllerName(self):
        """
        Returns the Model's Controller class name
        
        :returns: str
        """
        return self.controller.getControllerName()
    
    def getResourceID(self):
        """
        Returns the Model Resource ID that identifies the resource to the
        Controller
        
        :returns: str
        """
        return self.resID

    def getVendorID(self):
        """
        Returns the Resource Vendor ID that is used to find compatible Models 
        
        :returns: str
        """
        return self.VID
    
    def getProductID(self):
        """
        Returns the Resource Product ID that is used to find compatible Models 
        
        :returns: str
        """
        return self.PID
    
    def getProperties(self):
        return { 'deviceType': self.deviceType,
                 'deviceVendor': 'Generic',
                 'deviceModel': 'Device',
                 'deviceSerial': 'Unknown',
                 'deviceFirmware': 'Unknown'
                }
        
