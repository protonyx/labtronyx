import sys
# System Imports
import os
import importlib
import subprocess
import time
import logging
import logging.handlers

# Instrument Control Classes
import common
from common import is_valid_ipv4_address, resolve_hostname
from common.rpc import RpcClient

class InstrumentControl(object):
    """
    InstrumentControl is a helper class that provides functionality to 
    communicate with any number of local or remote InstrumentManager instances.
    
    InstrumentControl simplifies the process of writing test instrument
    automation and control scripts. This is accomplished by abstracting the
    communication with :class:`InstrumentManager` instances that contain the device
    interface code. 
    
    Dependencies:
    - InstrumentManager must be running on the local or remote machine that you
    are trying to connect to. :func:`InstrumentControl.startWaitManager` can be
    used to spawn a new process of InstrumentManager.
    
    Example with InstrumentManager already running: ::
        from InstrumentControl import InstrumentControl
        instr = InstrumentControl()
        
    Example with InstrumentManager not already running: ::
        from InstrumentControl import InstrumentControl
        instr = InstrumentControl()
        instr.startWaitManager()
        
    """
    managers = {} # IP Address -> Manager RPC Client object
    hostnames = {} # Hostname => IP Address [Lookup table]
    
    # Resources
    resources = {} # { Address -> { Resource UUID -> (Controller, ResourceID) } } 
    instruments = {} # { Resource UUID -> RpcClient objects }
    properties = {} # { Resource UUID -> Properties (dict) }
    
    def __init__(self, **kwargs):
        """
        :param Logger: Logger instance if you wish to override the internal instance
        :type Logger: Logging.logger
        """
        # Get the root path
        can_path = os.path.dirname(os.path.realpath(__file__)) # Resolves symbolic links
        rootPath = os.path.abspath(can_path)
        configPath = os.path.join(rootPath, 'config')
        configFile = os.path.join(configPath, 'default.py')
        
        try:
            import imp
            cFile = imp.load_source('default', configFile)
            self.config = cFile.Config()
            self.config.rootPath = rootPath
            
        except Exception as e:
            print("FATAL ERROR: Unable to import config file")
            sys.exit()

         # Setup Logger
        if 'Logger' in kwargs:
            self.logger = kwargs['Logger']
        
        else:
            #loggerList = logging.Logger.manager.loggerDict
            # Attach to the MTB/MIST logger if inside a test environment
            #if '__main__' in loggerList:
            #self.logger = logging.getLogger('__main__')
            
            self.logger = logging.getLogger(__name__)
            formatter = logging.Formatter(self.config.logFormat)
                    
             # Configure logging level
            self.logger.setLevel(self.config.logLevel_console)
                
            # Logging Handler configuration, only done once
            if self.logger.handlers == []:
                # Console Log Handler
                lh_console = logging.StreamHandler(sys.stdout)
                lh_console.setFormatter(formatter)
                lh_console.setLevel(self.config.logLevel_console)
                self.logger.addHandler(lh_console)
                
        # Attempt to start the local manager
        #self.startWaitManager()
                
        # Attempt to connect to the local manager
        local = self.getAddressFromHostname('localhost')
        self.addManager(local)
        
        #=======================================================================
        # # Dependency Check
        # # Numpy
        # try:
        #     importlib.import_module('numpy')
        # except ImportError:
        #     self.logger.error('Unable to import Numpy. Non-fatal for the moment.')
        # # MatPlotLib
        # 
        # self.logger.info("Dependency check complete")
        #=======================================================================
    
    #===========================================================================
    # Manager Operations    
    #===========================================================================
    
    def getAddressFromHostname(self, hostname):
        """
        Resolves a hostname.
        
        :param hostname: Machine hostname to resolve
        :type hostname: str
        :returns: str -- IPv4 Address
        """
        addr = self.hostnames.get(hostname, None)
        if addr is None:
            addr = resolve_hostname(hostname)
            
        return addr
    
    def isConnectedHost(self, hostname):
        """
        Check if a given hostname is connected
        
        :param hostname: hostname to check
        :type hostname: str
        :returns: True is hostname if connected, False otherwise
        """
        if self.hostnames.get(hostname, None) is not None:
            return True
        else:
            return False
    
    def getAddressFromUUID(self, uuid):
        """
        Get the host address of a resource.
        
        :param uuid: Resource UUID
        :type uuid: str
        :returns: IP Address of host associated with the given resource or None
        if the resource was not found
        """
        dev_man = self._getManager_uuid(uuid)
        if dev_man is not None:
            return dev_man._getAddress()
        else:
            return None
    
    def getHostnames(self):
        """
        Get a list of connected hostnames
        
        :returns: List of connected hostnames
        """
        return self.hostnames.keys()
    
    #===========================================================================
    # Local Manager Operations
    #===========================================================================
    
    def startManager(self):
        """
        Start a local instance of :class:`InstrumentManager` using 
        :func:`subprocess.Popen`.
        
        No attempt is made to check whether an :class:`InstrumentManager`
        process is already running. The default behavior for :class:'InstrumentManager'
        is to exit when the port is already in use.
        
        See :class:'InstrumentManager' documentation for more information. 
        
        .. note:: 
           This function does not block! If the :class:`InstrumentManager`
           instance is not fully initialized before attempting to connect to it,
           timeouts will occur. 
        """
        local = self.getAddressFromHostname('localhost')
        
        try:
            pyExec = sys.executable
            manPath = os.path.join(self.rootPath, 'InstrumentManager.py')
            
            subprocess.Popen([pyExec, manPath])
            
        except:
            pass
            
    def startWaitManager(self, timeout=10.0):
        """
        Start a local instance of :class:`InstrumentManager` using 
        :func:`subprocess.Popen`. This function will block until the manager is
        fully initialized. 
        
        See :func:`startManager` for more.
        
        :param timeout: Maximum number of seconds to wait before timeout occurs  
        :type timeout: float
        :returns: Nothing
        """
        local = self.getAddressFromHostname('localhost')
        
        self.startManager()
        
        tryTime = 0.0
        waitTime = 2.0
        
        while not self.managerRunning(local):
            tryTime += waitTime
            time.sleep(waitTime)
            if tryTime >= timeout:
                break
        
    def managerRunning(self, address, port=None):
        """
        Check if an :class:`InstrumentManager` instance is running. Attempts to
        open a socket to the provided address and port.
        
        :param address: IP Address to check
        :type address: str
        :param port: Port
        :type port: int
        :returns: True if running, False if not running
        """
        man = self.getManager(address)
        if man is not None:
            # Manager already connected
            return True
        else:
            # Try to connect to one
            if self.addManager(address, port):
                # Manager connected
                self.removeManager(address)
                return True
            else:
                # No manager could be found at the address:port
                return False
    
    def stopManager(self, address, port=None):
        man = self.getManager(address)
        if man is not None:
            man.rpc_stop()
            self.removeManager(address)
        else:
            if self.addManager(address, port):
                man = self.getManager(address)
                man.rpc_stop()
                self.removeManager(address)
            else:
                # No manager could be found at the address:port
                pass
    
    def addManager(self, address, port=None):
        """
        Attempts to find a manager instance at the given address
        
        If a manager is found, get the list of resources
        
        Returns:
            - True if manager found, false if connection failed
        """
        
        seekPort = port or self.config.managerPort
        
        # Check address or resolve hostname
        if is_valid_ipv4_address(address):
            addr = address
        else:
            addr = resolve_hostname(address)
        
        # Attempt a connection
        try:
            testManager = RpcClient(address=addr, port=seekPort)
            if not testManager._ready():
                return False
        except:
            return False
        
        else:
            self.hostnames[testManager.hostname] = addr 
            self.managers[addr] = testManager
            self.refreshManager(addr)
            
        return True
        
    def refreshManager(self, address=None):
        """
        Retrieves the list of resources for the device. If no address is
        provided, recursively refresh all managers
        
        TODO: Create logic to group items by hostname, type, vendor or model
        """
        
        if address in self.managers:
            man = self.managers.get(address)
            
            # Force a remote device scan
            man.refresh()
            
            # Get the list of resources for the address
            cached_resources = self.resources.get(address, {})
            
            # Get resources from the remote manager
            remote_resources = man.getResources() or {}

            # Purge resources that are no longer available
            for uuid, res in cached_resources.items():
                if uuid not in remote_resources:
                    cached_resources.pop(uuid)
                    
            # Add new resources
            for uuid, res in remote_resources.items():
                if uuid not in cached_resources.keys():
                    cached_resources[uuid] = res
                    
            # Update the resource cache
            self.resources[address] = cached_resources

        elif address is None:
            for addr in self.managers:
                self.refreshManager(addr)
                 
        else:
            return False
        
        return True
    
    def removeManager(self, address):
        """
        Disconnects from the given manager
        """
        if self.managers.has_key(address):
            # Remove all resources from that host
            cached_resources = self.resources.pop(address, {})
            
            for uuid, res in cached_resources.items():
                self.destroyInstrument(uuid)
                    
                self.properties.pop(uuid, None)
                
            # Remove host
            rpc_client = self.managers.pop(address, None)
            del rpc_client
            
            return True
        
        else:
            return False
        
    def getManager(self, address):
        return self.managers.get(address, None)
            
    def _getManager_uuid(self, res_uuid):
        dev_man = None
        for addr, res_dict in self.resources.items():
            if res_uuid in res_dict.keys():
                dev_man = self.managers.get(addr, None)
        
        return dev_man
    #===========================================================================
    # Resource Operations
    #===========================================================================
    
    def getResources(self, address=None):
        """
        Get a dictionary of resources from one or all connected instrument
        managers
        
        Parameters:
        - address (optional): str IP Address
        
        Returns:
        -dict of resource objects by uuid
        """
        if address in self.managers:
            return self.resources.get(address, {})
        
        elif address is None:
            ret = {}
            for addr in self.managers:
                res = self.resources.get(addr, {})
                ret.update(res)
            return ret
        
        else:
            return {}
        
    def getResource(self, res_uuid):
        """
        Returns the contents of the resource dictionary for the given UUID
        
        Returns:
        - Tuple (controller, resID)
        """
        # Iterate through all resources to find
        for address in self.resources:
            addr_res = self.resources.get(address, {})
            for uuid, res in addr_res.items():
                if uuid == res_uuid:
                    return res
                
        return None
    
    def addResource(self, address, controller, VendorID, ProductID):
        """
        Manually create a resources on an instrument manager
        
        If the controller does not support manually adding resources, this 
        function will return False
        
        Parameters:
        - address: str IP Address
        - controller: str
        - VendorID: str
        - ProductID: str
        
        Returns:
        - bool: True if success or False if failed
        """
        if address in self.managers:
            man = self.managers.get(address)
            
            # Does manager support manually adding resources?
            if man.canEditResources(controller):
                man.addResource(controller, VendorID, ProductID)
            res_dict['address'] = address
            res_dict['hostname'] = self.managers.get(address).hostname
        
            self.resources[res_uuid] = res_dict
            return True
        
        else:
            return False
    
    def removeResource(self, address, res_uuid):
        if self.resources.has_key(res_uuid):
            self.resources.pop(res_uuid, None)
            
        # Instrument may not exist, but just in case
        self.destroyInstrument(res_uuid)
            
    
    #===========================================================================
    # Instrument Operations
    #
    # Instruments are RPC Client objects to local/remote instruments
    #===========================================================================
    
    def getInstrument(self, res_uuid):
        return self.instruments.get(res_uuid, None)
    
    def loadModel(self, uuid, modelName=None, className=None):
        dev_man = self._getManager_uuid(uuid)
        
        if dev_man is not None:
            return dev_man.loadModel(uuid, modelName, className)
        
        else:
            return False
        
    def unloadModel(self, uuid):
        dev_man = self._getManager_uuid(uuid)
        
        if dev_man is not None:
            ret = dev_man.unloadModel(uuid)
            self.refreshProperties(uuid)
            return ret
        
        else:
            return False
    
    def createInstrument(self, res_uuid):
        """
        Checks if a resource has loaded a driver and started a RPC server
        
        If so, creates a RPC Client, adds it to the instrument dictionary and
        returns a reference to the RPC Client object
        """
        # Does an instrument already exist?
        instr = self.instruments.get(res_uuid, None)
        
        if instr is not None:
            return instr
        
        else:
            # Find out where this resource is located
            dev_man = self._getManager_uuid(res_uuid)
            addr = dev_man._getAddress()
                    
            if dev_man is not None:
                res_model = dev_man.getResourceModelName(res_uuid)
                
                if res_model is not None:
                    # A model is loaded, get the port
                    # The manager will automattically start the RPC server
                    port = dev_man.getResourcePort(res_uuid)
                    
                    try:
                        testInstrument = RpcClient(address=addr, port=port)
                        if testInstrument._ready():
                            self.instruments[res_uuid] = testInstrument
                            return testInstrument
                        
                        else:
                            return None
                    except:
                        return None
                    
                else:
                    # No model loaded for that resource
                    return None
                
            else:
                # The resource could not be located
                return None
    
    def destroyInstrument(self, res_uuid):
        """
        Unloads an instrument RPC Client
        
        Returns True if an instrument was deleted, otherwise False
        """
        instr = self.instruments.pop(res_uuid, None)
        if instr is not None:
            instr._close()
            del instr
            return True
        
        return False
    
    def refreshProperties(self, ResUUID=None):
        """
        Will attempt to create instruments for all resources to refresh property
        dictionaries
        """
        if ResUUID is None:
            ret = {}
            for addr, res_dict in self.resources.items():
                for uuid in res_dict:
                    ret[uuid] = self.refreshProperties(uuid)
                    
            return ret
        
        else:
            ret = {}
            instr = self.getInstrument(ResUUID)
            
            # Prevent the manager from maintaining an unreasonable number of
            # connections if we only need to grab properties data
            instr_destroyOnCompletion = False
            if instr is None:
                instr_destroyOnCompletion = True
                instr = self.createInstrument(ResUUID)
            
            if instr is None:
                # Model is not loaded for that resource
                ret['uuid'] = ResUUID
                c_name, res_id = self.getResource(ResUUID)
                ret['controller'] = c_name
                ret['resourceID'] = res_id
                # Get address and hostname from manager
                try:
                    dev_man = self._getManager_uuid(ResUUID)
                    ret['address'] = dev_man._getAddress()
                    ret['hostname'] = dev_man._getHostname()
                    
                except:
                    pass
                
            else:
                try:
                    ret = instr.getProperties()
                    # Inject hostname and address
                    ret['address'] = instr._getAddress()
                    ret['hostname'] = instr._getHostname()
                    
                except:
                    pass
                
            if instr_destroyOnCompletion:
                self.destroyInstrument(ResUUID)
                
            self.properties[ResUUID] = ret
            return ret
            
    def getProperties(self, ResUUID=None):
        """
        return the properties dictionary for all connected instruments
        
        If ResUUID is specified, a single dictionary will be returned
        
        If ResUUID is not specified, property dictionaries will be nested by UUID
        
        Returns None if the UUID is invalid or no properties have been queried
        for that UUID
        """
        if ResUUID in self.properties:
            return self.properties.get(ResUUID, None)
        
        else:
            return self.properties
    
    def getInstrument_list(self):
        """
        Returns a list of all enumerated instruments
        """
        for addr, res_dict in self.resources.items():
            for uuid in res_dict:
                self.createInstrument(uuid)
       
        return self.instruments.values()
    
    def getInstrument_serial(self, serial_number):
        """
        Returns an enumerated instrument that matches the serial number provided
        
        Return the first matching device
        """
        self.refreshProperties()
        
        for res_uuid, prop_dict in self.getProperties().items():
            if prop_dict['deviceSerial'] == serial_number:
                return self.createInstrument(res_uuid)
        
        return None
    
    def getInstrument_model(self, model_number):
        """
        Returns a list of enumerated instruments with the given model
        """
        self.refreshProperties()
        ret = []
        
        for res_uuid, prop_dict in self.getProperties().items():
            if prop_dict['deviceModel'] == model_number:
                ret.append(self.createInstrument(res_uuid))
                
        return ret
    
    def getInstrument_type(self, d_type):
        """
        Iterates of the list of enumerated instruments and returns a list of instruments that have types which match
        """
        self.refreshProperties()
        ret = []
        
        for res_uuid, prop_dict in self.getProperties().items():
            if prop_dict['deviceType'] == d_type:
                ret.append(self.createInstrument(res_uuid))
                
        return ret
    
    #===========================================================================
    # def startGUI(self):
    #     """
    #     Blocking operations which starts the InstrumentControl manager GUI.
    #     
    #     Depends on a manager running with RPC
    #     """
    #     try:
    #         man = self.getLocalManager()
    #         man.rpc_start()
    #         man_port = man.rpc_getPort()
    #         
    #         main = importlib.import_module('views.v_Main')
    #         main_gui = getattr(main, 'v_Main')(port=man_port)
    #         main_gui.start()
    #     except:
    #         self.logger.exception('Unable to start Instrument Control GUI')
    #===========================================================================
    
    
# Load GUI in interactive mode
if __name__ == "__main__":
    # Launch InstrumentControl GUI
    try:
        #sys.path.append("..")
        from application.a_Main import a_Main
        main_gui = a_Main()
        
    except Exception as e:
        print "Unable to load main application"
        raise
        sys.exit()

    
    #scope = instr.getInstrument_model("MSO5204")[0]
    #scope.getWaveform()
    #scope.exportWaveform(Filename='C:/temp/test.csv')
    #scope_gui = scope.loadView()
    

    
    