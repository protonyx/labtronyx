import uuid
import time

import common
import common.rpc

import threading

class c_Base(object):

    # TODO: Controllers will have hooks into the persistence config to "remember" how
    #       a particular device is configured when the program is run in the future.
    
    resources = {}
    
    def __init__(self, manager):
        """
        :param manager: Reference to the InstrumentManager instance
        :type manager: InstrumentManager object
        """
        common_globals = common.ICF_Common()
        self.config = common_globals.getConfig()
        self.logger = common_globals.getLogger()
        
        self.manager = manager
        
        self.e_alive = threading.Event()
        
    #===========================================================================
    # Controller Thread
    #===========================================================================
    
    def __thread_run(self):
        while(self.e_alive.isSet()):
            
            self.refresh()
            
            time.sleep(60.0)
            
    def startThread(self):
        self.e_alive.set()
            
        self.__controller_thread = threading.Thread(name=self.getControllerName(), target=self.__thread_run)
        self.__controller_thread.start()
        
    def stopThread(self):
        self.e_alive.clear()
        self.__controller_thread.join()

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
        Get a listing of resources by ID. There is no requirement for how
        resources are stored internal to the controller, but this function
        should return a dict with the format::
        
            { resourceID: (VID, PID) }
        
        :returns: dict
        """
        raise NotImplementedError
    
    def canEditResources(self):
        """
        Query the controller to find out if that controller supports manually
        adding and destroying resources. 
        """
        raise NotImplementedError
    
    def openResourceObject(self, resID, **kwargs):
        """
        Return an open resource object for a Model to interact with the
        controller through. Additional parameters may be required, depending
        on the needs of the controller
        
        :param resID: Resource ID
        :type resID: str
        :returns: object
        """
        raise NotImplementedError
        
    def closeResourceObject(self, resID):
        """
        Close a resource object and free any associated system resources.
        
        :param resID: Resource ID
        :type resID: str
        :returns: object
        """
        raise NotImplementedError
    
    #===========================================================================
    # Automatic Controllers
    #===========================================================================
    
    def refresh(self):
        """
        Refreshes the resource list. If resources are no longer available,
        they should be removed.
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

class r_Base(common.rpc.RpcBase):
    type = "Generic"
    
    def __init__(self, resID, controller, **kwargs):
        common.rpc.RpcBase.__init__(self)
        
        common_globals = common.ICF_Common()
        self.config = common_globals.getConfig()
        self.logger = common_globals.getLogger()
        
        self.uuid = str(uuid.uuid4())
        
        self.groupTag = kwargs.get('groupTag', '')
        
        self.model = None
        self.resID = resID
        self.controller = controller
        
        self.rpc_start()
        
    def getUUID(self):
        return self.uuid
    
    def getResID(self):
        return self.resID
    
    def getType(self):
        return self.type
    
    def getStatus(self):
        # TODO: Resource status
        pass
    
    def getPort(self):
        try:
            # Start the RPC server if it isn't already started
            if not self.rpc_isRunning():
                self.rpc_start()    
            
            return self.rpc_getPort()
        
        except:
            pass
    
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
        # TODO
        
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
    
    def getModels(self):
        """
        Get a list of models that are compatible with this resource
        
        :returns: list
        """
        pass
    
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
            self.model.rpc_start()
            
            return True

        except:

            self.logger.exception('Failed to load model: ', modelName)
            return False
    
    def unloadModel(self):
        """
        If a Model is currently loaded for the resource, unload the resource.
        
        :returns: True if successful, False otherwise
        """
        if self.model is not None:
            try:
                self.model._onUnload()
                self.model.rpc_stop()
                
            except:
                self.logger.exception('Exception while unloading model')
                
            del self.model
            self.model = None
                
            return True
        
        else:
            return False