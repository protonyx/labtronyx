import uuid
import time
import threading
import importlib

import common
import common.rpc as rpc

class c_Base(object):

    # TODO: Controllers will have hooks into the persistence config to "remember" how
    #       a particular device is configured when the program is run in the future.
    
    REFRESH_RATE = 60.0 # Seconds
    
    def __init__(self, manager):
        """
        :param manager: Reference to the InstrumentManager instance
        :type manager: InstrumentManager object
        """
        common_globals = common.ICF_Common()
        self.config = common_globals.getConfig()
        self.logger = common_globals.getLogger()
        
        self.resources = {}
        self.manager = manager
        
        self.e_alive = threading.Event()
        self.e_alive.set()
            
        self.__controller_thread = threading.Thread(name=self.getControllerName(), target=self.__thread_run)
        self.__controller_thread.start()
        
    def __del__(self):
        self.e_alive.clear()
        self.__controller_thread.join()
        
    #===========================================================================
    # Controller Thread
    #===========================================================================
    
    def __thread_run(self):
        while(self.e_alive.isSet()):
            
            self.refresh()
            
            time.sleep(self.REFRESH_RATE)
            
    #===========================================================================
    # Controller Methods
    #===========================================================================

    def getControllerName(self):
        return self.__class__.__name__

    # Inheriting classes must implement these functions:
    def open(self):
        """
        Controller Initialization
        
        Make any system driver calls necessary to initialize communication. If
        any kind of exception occurs that will inhibit communication, this
        function should return False to indicate an error to the 
        InstrumentManager.
        
        Any exceptions raised will be caught by the InstrumentManager, and it
        will be assumed that the controller failed to initialize. A subsequent
        call to :func:`close` will be made in this case.
        
        :returns: bool - True if ready, False if error occurred
        """
        raise NotImplementedError
    
    def close(self):
        """
        Controller clean-up
        
        Make any system driver calls necessary to clean-up controller
        operations. This function should explicitly free any system resources
        to prevent locking errors.
        
        Any exceptions raised will be caught by the InstrumentManager.
        """
        raise NotImplementedError

    def getResources(self):
        """
        Get the dictionary of resources by ID.
        
        :returns: dict
        """
        raise NotImplementedError
    
    def canEditResources(self):
        """
        Query the controller to find out if that controller supports manually
        adding and destroying resources. 
        """
        raise NotImplementedError
    
    #===========================================================================
    # Automatic Controllers
    #===========================================================================
    
    def refresh(self):
        """
        Refreshes the resource list. This function is called regularly by the
        controller thread.
        """
        raise NotImplementedError
    
    #===========================================================================
    # Manual Controllers
    #===========================================================================
    
    def addResource(self, ResID, VID, PID):
        """
        Manually add a resource to the controller
        
        :param ResID: Resource Identifier
        :type ResID: str
        :param VID: Vendor Identifier
        :type VID: str
        :param PID: Product Identifier
        :type PID: str
        :returns: bool - True if successful, False otherwise
        """
        raise NotImplementedError
    
    def destroyResource(self, ResID):
        """
        Remove a manually added resource
        
        :param ResID: Resource Identifier
        :type ResID: str
        :returns: bool - True if successful, False otherwise
        """
        raise NotImplementedError

class r_Base(object):
    type = "Generic"
    
    def __init__(self, resID, controller, **kwargs):
        
        common_globals = common.ICF_Common()
        self.config = common_globals.getConfig()
        self.logger = common_globals.getLogger()
        
        self.uuid = str(uuid.uuid4())
        self.status = 'INIT'
        
        self.groupTag = kwargs.get('groupTag', '')
        
        self.model = None
        self.resID = resID
        self.controller = controller
        
        # Start RPC Server
        self.rpc_server = rpc.RpcServer(name='%s-%s' % (controller.getControllerName(), resID),
                                        logger=self.logger)
        self.rpc_server.registerObject(self)
        
    def getUUID(self):
        return self.uuid
    
    def getResID(self):
        return self.resID
    
    def getType(self):
        return self.type
    
    def getStatus(self):
        return self.status
    
    def getControllerName(self):
        """
        Returns the Resource's Controller class name
        
        :returns: str
        """
        return self.controller.getControllerName()
    
    def getPort(self):
        # Start the RPC server if it isn't already started
        if self.rpc_server.rpc_isRunning():
            return self.rpc_server.rpc_getPort()
    
    def getProperties(self):
        res_prop = {
            'uuid': self.uuid,
            'controller': self.controller.getControllerName(),
            'resourceID': self.resID,
            'resourceType': self.type,
            'groupTag': self.groupTag,
            'status': self.getStatus(),
            'port': self.getPort()
            }
        
        # Append Model properties if a Model is loaded
        if self.model is not None:
            model_prop = self.model.getProperties()
            
            model_prop['modelName'] = self.model.getModelName()
            
            res_prop.update(model_prop)
        
        return res_prop
    
    #===========================================================================
    # Resource State
    #===========================================================================
    
    def isOpen(self):
        raise NotImplementedError
        
    def open(self):
        """
        Open the resource
        
        :returns: True if open was successful, False otherwise
        """
        raise NotImplementedError
    
    def close(self):
        """
        Close the resource
        
        :returns: True if close was successful, False otherwise
        """
        raise NotImplementedError
    
    def lock(self):
        raise NotImplementedError
    
    def unlock(self):
        raise NotImplementedError
    
    #===========================================================================
    # Data Transmission
    #===========================================================================
    
    def write(self, data):
        raise NotImplementedError
    
    def read(self):
        raise NotImplementedError
    
    def query(self):
        raise NotImplementedError
    
    #===========================================================================
    # Models
    #===========================================================================
    
    def hasModel(self):
        return self.model is not None
    
    def loadModel(self, modelName):
        """
        Load a Model. A Model name can be specified to load a specific model,
        even if it may not be compatible with this resource. Reloads model
        when importing, in case an update has occured.
        
        Example::
        
            instr.loadModel('Tektronix.Oscilloscope.m_DigitalPhosphor')
        
        :param modelName: Module name of the desired Model
        :type modelName: str
        :returns: True if successful, False otherwise
        """
        try:
            # Check if the specified model is valid
            testModule = importlib.import_module(modelName)
            reload(testModule) # Reload the module in case anything has changed
            
            className = modelName.split('.')[-1]
            testClass = getattr(testModule, className)
            
            self.model = testClass(self)
            self.model._onLoad()
            
            # RPC register object
            self.rpc_server.registerObject(self.model)
            
            return True

        except:

            self.logger.exception('Failed to load model: %s', modelName)
            return False
    
    def unloadModel(self):
        """
        If a Model is currently loaded for the resource, unload the resource.
        
        :returns: True if successful, False otherwise
        """
        if self.model is not None:
            try:
                self.model._onUnload()
                # RPC unregister object
                
                self.rpc_server.unregisterObject(self.model)
                
            except:
                self.logger.exception('Exception while unloading model')
                
            del self.model
            self.model = None
                
            return True
        
        else:
            return False
