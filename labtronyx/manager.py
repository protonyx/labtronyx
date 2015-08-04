# System Imports
import os, sys
import time
import socket
import copy
import importlib
import threading
import logging, logging.handlers

# Local Imports
from . import logger
import drivers
import interfaces
import common
import version

__all__ = ['InstrumentManager']

class InstrumentManager(object):
    """
    Labtronyx InstrumentManager

    Facilitates communication with instruments using all available interfaces.

    :param rpc: Enable RPC endpoint
    :type rpc: bool
    :param rpc_port: RPC endpoint port
    :type rpc_port: int
    :param logger: Logger instance if you wish to override the internal instance
    :type logger: Logging.logger
    """
    name = 'Labtronyx'
    longname = 'Labtronyx Instrumentation Control Framework'
    
    def __init__(self, **kwargs):
        # Initialize instance variables
        self._interfaces = {} # Interface name -> interface object
        self._drivers = {} # Module name -> Model info
        self.rpc_server = None

        # Configurable instance variables
        self.rpc_port = kwargs.get('rpc_port', 6780)
        self.logger = kwargs.get('logger', logger)

        # Initialize PYTHONPATH
        self.rootPath = os.path.dirname(os.path.realpath(os.path.join(__file__, os.curdir)))
        
        if not self.rootPath in sys.path:
            sys.path.append(self.rootPath)

        # Announce Version
        self.logger.info(self.longname)
        self.logger.info("Version: %s", version.ver_full)
        self.logger.debug("Build Date: %s", version.build_date)

        #
        # Load Plugins
        #
        
        # Load Drivers
        #self.drivers = drivers.getAllDrivers()
        self._drivers = self.__scan(drivers)
        
        for driver in self._drivers.keys():
            self.logger.debug("Found Driver: %s", driver)
        
        # Load Interfaces
        interface_info = self.__scan(interfaces)
        
        for interf in interface_info.keys():
            self.logger.debug("Found Interface: %s", interf)
            self.enableInterface(interf)

        #
        # Start RPC Server
        #
        if kwargs.get('rpc', True):
            if not self.rpc_start():
                raise RuntimeError("Unable to start RPC Server")
    
    def __del__(self):
        self.rpc_stop()

    def __scan(self, pkg):
        """
        Scan a package for valid plug-in modules. Plugin modules have a class with the same name as the module and
        each class has an attribute "info" (dict) that is cataloged.
        
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

                except ImportError:
                    # Missing dependencies, skip this plugin
                    self.logger.error("Unable to import %s", pkg_name)
                    
                except Exception as e:
                    self.logger.exception("Exception during module scan: %s", pkg_name)

        return plugins

    #===========================================================================
    # RPC Server
    #===========================================================================

    def rpc_start(self):
        """
        Start the RPC Server and being listening for remote connections.

        :returns: True if successful, False otherwise
        """
        # Clean out old RPC server, if any exists
        if hasattr(self, 'rpc_server'):
            self.rpc_stop()

        self.rpc_server = None
        self.rpc_server_thread = None

        # Attempt to import ptx-rpc
        try:
            import ptxrpc as rpc

            self.rpc_server = rpc.PtxRpcServer(host='localhost',
                                               port=self.rpc_port,
                                               logger=self.logger)

            # Register InstrumentManager in the base path
            self.rpc_server.register_path('/', self)
            self.logger.debug("RPC Server starting...")

            # Register all resources with the RPC server
            self.rpc_refresh()

            # Start the server in a new thread
            self.rpc_server_thread = threading.Thread(name='Labtronyx-InstrumentManager',
                                                      target=self.rpc_server.serve_forever)
            self.rpc_server_thread.start()

            return True

        except ImportError:
            return False

        except rpc.RpcServerPortInUse:
            self.logger.error("RPC Port in use, shutting down...")
            return False

        except Exception as e:
            self.logger.exception("RPC Exception")
            return False

    def rpc_refresh(self):
        """
        Re-register all resources with the RPC server

        :return: None
        """
        if self.rpc_server is not None:
            for interf in self._interfaces.values():
                try:
                    for res_uuid, res_obj in interf.getResources.items():
                        self.rpc_server.register_path(res_uuid, res_obj)

                except:
                    pass

    def rpc_stop(self):
        """
        Stop the RPC Server. Attempts to shutdown and free
        all resources.
        """
        if self.rpc_server is not None:
            self.logger.debug("RPC Server stopping...")

            # Close all interfaces
            for interface in self._interfaces.keys():
                self.disableInterface(interface)

            # Stop the InstrumentManager RPC Server
            self.rpc_server.shutdown()
            self.rpc_server.server_close()
            self.rpc_server_thread.join()

            # Signal the event
            self._event_signal(common.events.Manager_Shutdown())

            self.rpc_server = None
            self.rpc_server_thread = None
            
    def getVersion(self):
        """
        Get the Labtronyx version
        
        :returns: str
        """
        return version.ver_full
    
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
    # Event Processing and Dispatch
    #===========================================================================

    def _event_signal(self, event, **kwargs):
        """
        Private method called internally to signal events. Calls handlers and dispatches event signal to subscribed
        clients

        :param event: event object
        :param kwargs: arguments
        :return:
        """
        pass

    def addEventHandler(self, event, handler):
        pass

    def removeEventHandler(self, event):
        pass

    #===========================================================================
    # Interface Operations
    #===========================================================================

    @property
    def interfaces(self):
        return self._interfaces


    def getInterfaces(self):
        """
        Get a list of interfaces that are enabled
        
        :returns: list
        """
        return self._interfaces.keys()
    
    def enableInterface(self, interface):
        if interface not in self._interfaces:
            try:
                interfaceModule = importlib.import_module(interface)

                # Look for a class with the same name as the module
                # TODO: Find a way to have multiple classes per file
                className = interface.split('.')[-1]
                interfaceClass = getattr(interfaceModule, className)

                # Instantiate interface
                inter = interfaceClass(manager=self,
                                       logger=self.logger)

                # Call the plugin hook to open the interface
                inter.open()

                self.logger.info("Started Interface: %s" % interface)
                self._interfaces[interface] = inter
            except:
                self.logger.exception("Exception during interface open")
                
        else:
            raise RuntimeError("Interface is already running!")
    
    def disableInterface(self, interface):
        if interface in self._interfaces:
            try:
                inter = self._interfaces.pop(interface)

                # Call the plugin hook to close the interface
                inter.close()

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

        :returns: bool
        """
        for interf in self._interfaces.values():
            try:
                # Discover any new resources
                interf.enumerate()

                # Refresh each resource
                for res in interf.getResources():
                    res.refresh()

            except Exception as e:
                self.logger.exception("Unhandled exception during refresh of interface: %s", interf.name)

        self.rpc_refresh()
            
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

        for interf in self._interfaces.values():
            try:
                for uuid, res in interf.resources.items():
                    ret[uuid] = res.getProperties()

                    ret[uuid].setdefault('deviceType', '')
                    ret[uuid].setdefault('deviceVendor', '')
                    ret[uuid].setdefault('deviceModel', '')
                    ret[uuid].setdefault('deviceSerial', '')
                    ret[uuid].setdefault('deviceFirmware', '')

            except NotImplementedError:
                pass
        
        return ret
    
    def getResource(self, res_uuid):
        """
        Returns a resource object given the Resource UUID
                
        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: object
        """
        # NON-SERIALIZABLE
        for interf in self._interfaces.values():
            try:
                temp = interf.resources.get(res_uuid)
                if temp is not None:
                    return temp

            except:
                pass

        return None
    
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
            int_obj = self._interfaces.get(interface)
            return int_obj.addResource(ResID)
        
        except:
            return False

    #===========================================================================
    # Driver Operations
    #===========================================================================

    @property
    def drivers(self):
        return self._drivers
                
    def getDrivers(self):
        """
        Get a list of valid drivers found during the initial driver scan.

        :return: dict
        """
        return self._drivers
    
if __name__ == "__main__":
    # Interactive Mode
    import labtronyx
    labtronyx.logConsole()

    # Instantiate an InstrumentManager
    man = labtronyx.InstrumentManager(rpc=True)
    
    # Keep the main thread alive
    while(1):
        time.sleep(1.0)
