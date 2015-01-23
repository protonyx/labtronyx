"""
Model Base Class
"""

import common
import common.rpc

import time
import sys
import importlib
import logging
import threading

import views

class m_Base(object):
    
    deviceType = 'Generic'

    # Model Lookup
    validControllers = []
    validVIDs = []
    validPIDs = []
    
    # Collector Attributes
    _collector_thread = None
    _collector_lock = threading.Lock()
    _collectors = {}
    _collector_methods = {}
    
    def __init__(self, uuid, controller, resID, VID, PID, **kwargs):
        
        common_globals = common.ICF_Common()
        self.config = common_globals.getConfig()
        self.logger = common_globals.getLogger()
        
        self.uuid = uuid
        self.resID = resID
        self.VID = VID
        self.PID = PID
        
        # Controller Object
        self._controller_object = controller
        
        # Check for logger
        self.logger = kwargs.get('Logger', logging)
        
    #===========================================================================
    # Collector Functionality
    #===========================================================================
    
    def __collector_thread(self, lock_obj):
        """
        Asynchronous thread that automatically polls methods that are marked
        for collection
        """
        threading.current_thread().setName('collector_%s' % self.uuid)
        next_sample = {}
        
        while (len(self._collector_methods) > 0):
            wait_next = 1.0
            
            for method, collector_config in self._collector_methods.items():
                interval, depth = collector_config
                
                # Check if it is time to get a new sample
                sample_time = next_sample.get(method, 0.0)
                if time.time() > sample_time:
                    
                    if hasattr(self, method):
                        method_b = getattr(self, method)
                        ret = method_b()
                        
                        with lock_obj:
                            coll = self._collectors[method]
                            coll.append((sample_time, ret))
                            if len(coll) > depth:
                                coll.pop(0)
                        
                    else:
                        self.stopCollector(method)
                        self.logger.error("Collector error: invalid method %s", method)
                    
                    # Increment the next sample time
                    next_sample[method] = next_sample.get(method, time.time()) + interval
        
        # Clear reference to this thread before exiting
        self._collector_thread = None
        
    def startCollector(self, method, interval, depth):
        """
        Starts a Collector thread to retrieve data at a regular interval.
        
        :param method: Name of the Model method to invoke
        :type method: str
        :param interval: Interval in seconds between method invokations
        :type interval: float
        :param depth: Number of samples to keep
        :type depth: int
        :returns: Boolean, True if successful, False otherwise.
        """
        self._collector_methods[method] = (interval, depth)
        self._collectors[method] = []
        
        # Start the accumulator thread
        if self._collector_thread is None:
            self._collector_thread = threading.Thread(target=self.__collector_thread, args=(self._collector_lock,))
            self._collector_thread.start()
    
    def stopCollector(self, method):
        try:
            self._collector_methods.pop(method)
            self._collectors.pop(method)
        except:
            pass
        
    def getCollector(self, method, time=0.0):
        """
        Get all data from a collector after a certain timestamp
        
        :param method: Name of collector-attached method
        :type method: str
        :param time: Lower bound of time for returned samples
        :type time: float
        :return: list
        """
        if method in self._collector_methods:
            try:
                coll = self._collectors.get(method)
                
                for index, entry in enumerate(coll):
                    timestamp, _ = entry
                    
                    if timestamp > time:
                        return coll[index:] # Return a slice of the list after the list entry
                        
                return []
            
            except:
                self.logger.exception("Exception while retrieving collector data")
        
        else:
            return None
            
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
        fqn = self.__class__.__module__

        return fqn
    
        # Truncate class name from module
        #fqn_split = fqn.split('.')
        #return '.'.join(fqn_split[0:-1])
    
    def getUUID(self):
        """
        Returns the Resource UUID that is provided to the Model
        
        :returns: str
        """
        return self.uuid
    
    def getControllerObject(self):
        """
        Returns the Model's Controller object
        
        :returns: object
        """
        return self._controller_object
    
    def getControllerName(self):
        """
        Returns the Model's Controller class name
        
        :returns: str
        """
        return self._controller_object.getControllerName()
    
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
        return { 'modelName': self.getModelName(),
                 'controllerName': self.getControllerName(),
                 'deviceType': self.deviceType,
                 'deviceVendor': 'Generic',
                 'deviceModel': 'Device',
                 'deviceSerial': 'Unknown',
                 'deviceFirmware': 'Unknown'
                }
        
