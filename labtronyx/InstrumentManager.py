import os, sys
import time
import socket
import uuid
import copy
import importlib, inspect
import logging, logging.handlers

class InstrumentManager(object):
    """
    Labtronyx Instrument Manager

    Facilitates communication with instruments using all available interfaces.
    
    :param Logger: Logger instance if you wish to override the internal instance
    :type Logger: Logging.logger
    :param configFile: Configuration file to load
    :type configFile: str
    """
    drivers = {} # Module name -> Model info
    interfaces = {} # Interface name -> interface object
    resources = {} # UUID -> Resource Object
    
    def __init__(self, **kwargs):
        # Ensure library is present in PYTHONPATH
        self.rootPath = os.path.dirname(os.path.realpath(os.path.join(__file__, os.curdir)))
        
        if not self.rootPath in sys.path:
            sys.path.append(self.rootPath)
        
        # Load Config
        configFile = kwargs.get('configFile', 'default')
        try:
            cFile = importlib.import_module('config.%s' % configFile)
            self.config = cFile.Config()
            
        except Exception as e:
            print("FATAL ERROR: Unable to import config file")
            sys.exit()
        
        # Configure logger
        if 'Logger' in kwargs or 'logger' in kwargs:
            self.logger = kwargs.get('Logger') or kwargs.get('logger')
        
        else:
            self.logger = logging.getLogger(__name__)
            formatter = logging.Formatter(self.config.logFormat)
                    
             # Configure logging level
            self.logger.setLevel(self.config.logLevel_console)
                
            # File Log Handler
            if self.config.logToFile:
                if not os.path.exists(self.config.logPath):
                    os.makedirs(self.config.logPath)
                
                self.logFilename = os.path.normpath(os.path.join(self.config.logPath, 'InstrControl_Manager.log'))
                #===============================================================
                # if self.config.logFilename == None:
                #     self.logFilename = os.path.normpath(os.path.join(self.config.logPath, 'InstrControl_Manager.log'))
                # else:
                #     self.logFilename = os.path.normpath(os.path.join(self.config.logPath, self.config.logFilename))
                #===============================================================
                try:
                    fh = logging.handlers.RotatingFileHandler(self.logFilename, backupCount=self.config.logBackups)
                    fh.setLevel(self.config.logLevel_file)
                    fh.setFormatter(formatter)
                    self.logger.addHandler(fh)  
                    fh.doRollover()
                except Exception as e:
                    self.logger.error("Unable to open log file for writing: %s", str(e))
                    
        # Start the RPC Server
        self.enableRpc = kwargs.get('enableRpc', True) 
        if self.enableRpc == True:
            try:
                import common.rpc as rpc
                self.rpc_server = rpc.RpcServer(name='Labtronyx-InstrumentManager', 
                                                port=self.config.managerPort,
                                                logger=self.logger)
                self.rpc_server.registerObject(self)
                self.logger.debug("RPC Server starting...")
                
                for res_uuid, res_obj in self.resources.items():
                    res_obj.start()
    
            except rpc.RpcServerPortInUse:
                self.logger.error("RPC Port in use, shutting down...")
                sys.exit(1)
    
        # Announce Version
        self.logger.info(self.config.longname)
        self.logger.info("Instrument Manager, Version: %s", self.config.version)
        
        # Load Drivers
        import drivers
        #self.drivers = drivers.getAllDrivers()
        self.drivers = self.__scan(drivers)
        
        for driver in self.drivers.keys():
            self.logger.debug("Found Driver: %s", driver)
        
        # Load Interfaces
        import interfaces
        interface_info = self.__scan(interfaces)
        
        for interf in interface_info.keys():
            self.logger.debug("Found Interface: %s", interf)
            self.enableInterface(interf)
    
    def __del__(self):
        self.stop()
        
    def __scan(self, pkg):
        """
        Scan a package for valid plug-in modules.
        
        :param pkg: Package to scan
        :type pkg: package
        """
        import pkgutil
        plugins = {}
        
        for pkg_iter in pkgutil.walk_packages(path=pkg.__path__,
                                              prefix=pkg.__name__+'.'):
            pkg_imp, pkg_name, is_pkg = pkg_iter
        
            if not is_pkg:
                try:
                    # Use the filename as the class name
                    class_name = pkg_name.split('.')[-1]
                    
                    # Import the module
                    testModule = importlib.import_module(pkg_name)
                    
                    # Check to make sure the correct class exists
                    if hasattr(testModule, class_name):
                        testClass = getattr(testModule, class_name) # Will raise exception if doesn't exist
                        
                        if testClass != {}:
                            info = copy.deepcopy(testClass.info)
                            plugins[pkg_name] = info
                    
                except Exception as e:
                    self.logger.exception("Exception during module scan: %s", pkg_name)
                
        return plugins

    def start(self):
        """
        Start the RPC Server and being listening for remote connections.

        :returns: True if successful, False otherwise
        """
        self.enableRpc = True
        

    def stop(self):
        """
        Stop the RPC Server. Attempts to shutdown and free
        all resources.
        """
        self.EnableRPC = False
        self.logger.debug("RPC Server stopping...")

        # Close all resources
        for res in self.resources:
            try:
                res.close()
            except:
                pass
            
        # Close all interfaces
        for interface in self.interfaces.keys():
            self.disableInterface(interface)
                
        # Stop the InstrumentManager RPC Server
        if hasattr(self, 'rpc_server'):
            self.rpc_server.notifyClients('manager_shutdown')
            self.rpc_server.rpc_stop()
            
    def getVersion(self):
        """
        Get the Labtronyx version
        
        :returns: str
        """
        return self.config.version
    
    def getAddress(self):
        """
        Get the local IP Address
        """
        return socket.gethostbyname(self.getHostname())
    
    def getHostname(self):
        """
        Get the local hostname
        """
        return socket.gethostname()
        
    #===========================================================================
    # Interface Operations
    #===========================================================================
    
    def _cb_new_resource(self):
        """
        Notify InstrumentManager of the creation of a new resource. Called by
        controllers
        """
        for interface in self.interfaces.values():
            int_res = interface.getResources()
            for resID, res_obj in int_res.items():
            
                res_uuid = res_obj.getUUID()
        
                if res_uuid not in self.resources:
                    self.resources[res_uuid] = res_obj
                    
        if hasattr(self, 'rpc_server'):
            self.rpc_server.notifyClients('event_new_resource')

    def getInterfaces(self):
        """
        Get a list of controllers known to InstrumentManager
        
        :returns: list
        """
        return self.interfaces.keys()
    
    def enableInterface(self, interface):
        if interface not in self.interfaces:
            try:
                interfaceModule = importlib.import_module(interface)
                # TODO: Find a way to have multiple classes per file
                className = interface.split('.')[-1]
                interfaceClass = getattr(interfaceModule, className)
                inter = interfaceClass(self, logger=self.logger,
                                             config=self.config)
                inter.open()
                self.logger.info("Started Interface: %s" % interface)
                self.interfaces[interface] = inter
            except:
                self.logger.exception("Exception during interface open")
                
        else:
            raise RuntimeError("Interface is already running!")
    
    def disableInterface(self, interface):
        if interface in self.interfaces:
            try:
                inter = self.interfaces.pop(interface)
                inter.close()
                inter.stop()
                self.logger.info("Stopped Interface: %s" % interface)
                
            except:
                self.logger.exception("Exception during interface close")
                
        else:
            raise RuntimeError("Interface is not running!")
        
    #===========================================================================
    # Resource Operations
    #===========================================================================
    
    def refresh(self):
        """
        Signal all resources to refresh
        """
        for res in self.resources.values():
            try:
                res.refresh()
            except Exception as e:
                pass
            
        return True
    
    def refreshResources(self):
        """
        Alias for :func:`refresh`
        """
        return self.refresh()
    
    def getProperties(self):
        """
        Returns the property dictionaries for all resources
        
        :returns: dict
        """
        ret = {}
        for uuid, res in self.resources.items():
            ret[uuid] = res.getProperties()
            
            ret[uuid].setdefault('deviceType', '')
            ret[uuid].setdefault('deviceVendor', '')
            ret[uuid].setdefault('deviceModel', '')
            ret[uuid].setdefault('deviceSerial', '')
            ret[uuid].setdefault('deviceFirmware', '')
        
        return ret
    
    def getResource(self, res_uuid):
        """
        Returns a resource object given the Resource UUID
                
        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: object
        """
        # NON-SERIALIZABLE
        return self.resources.get(res_uuid)
    
    def getInstrument(self, res_uuid):
        """
        Alias for :func:`getResource`
        """
        # NON-SERIALIZABLE
        return self.getResource(res_uuid)
    
    def findResources(self, **kwargs):
        """
        Get a list of instruments that match the parameters specified.
        Parameters can be any key found in the resource property dictionary.

        :param uuid: Unique Resource Identifier (UUID)
        :param interface: Interface
        :param resourceID: Interface Resource Identifier (Port, Address, etc.)
        :param resourceType: Resource Type (Serial, VISA, etc.)
        :param deviceVendor: Instrument Vendor
        :param deviceModel: Instrument Model Number
        :param deviceSerial: Instrument Serial Number
        :returns: list of objects
        """
        # NON-SERIALIZABLE
        matching_instruments = []
        
        prop = self.getProperties()
        
        for uuid, res_dict in prop.items():
            match = True
            
            for key, value in kwargs.items():
                if res_dict.get(key) != value:
                    match = False
                    break
                
            if match:
                matching_instruments.append(self.getResource(uuid))
                
        return matching_instruments
    
    def findInstruments(self, **kwargs):
        """
        Alias for :func:`findResources`
        """
        # NON-SERIALIZABLE
        return self.findResources(**kwargs)
    
    def addResource(self, interface, ResID):
        """
        Manually add a resource to a controller. Not supported by all controllers
        
        .. note::
        
            This will return False if manually adding resources is not supported.
        
        :param interface: Interface name
        :type interface: str
        :param ResID: Resource Identifier
        :type ResID: str
        :returns: True if successful, False otherwise
        """
        try:
            int_obj = self.interfaces.get(interface)
            return int_obj.addResource(ResID)
        
        except:
            return False

    #===========================================================================
    # Driver Operations
    #===========================================================================
                
    def getDrivers(self):
        return self.drivers
    
if __name__ == "__main__":
    # Interactive Mode
    # Configure Logger
    logFormat = '%(asctime)s %(levelname)-8s %(module)s - %(message)s'
    logger = logging.getLogger(__name__)
    formatter = logging.Formatter(logFormat)
            
     # Configure logging level
    logger.setLevel(logging.DEBUG)
        
    # Logging Handler configuration, only done once
    if logger.handlers == []:
        # Console Log Handler
        lh_console = logging.StreamHandler(sys.stdout)
        lh_console.setFormatter(formatter)
        logger.addHandler(lh_console)
    
    man = InstrumentManager(logger=logger, enableRpc=True)
    
    # Keep the main thread alive
    try:
        while(1):
            time.sleep(1.0)
    except KeyboardInterrupt:
        man.stop()
