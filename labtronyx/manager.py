from __future__ import absolute_import

# System Imports
import os, sys
import time
import socket
import threading

# Local Imports
from . import bases
from . import logger
from . import common

try:
    from . import version
except ImportError:
    raise EnvironmentError("No Version file present, reinstall project")


class InstrumentManager(object):
    """
    Labtronyx InstrumentManager

    Facilitates communication with instruments using all available interfaces.

    :param rpc: Enable RPC endpoint
    :type rpc: bool
    :param rpc_port: RPC endpoint port
    :type rpc_port: int
    :param plugin_dirs: List of directories containing plugins
    :type plugin_dirs: list
    :param logger: Logger instance if you wish to override the internal instance
    :type logger: Logging.logger
    """
    name = 'Labtronyx'
    longname = 'Labtronyx Instrumentation Control Framework'
    
    def __init__(self, **kwargs):
        # Initialize instance variables
        self._interfaces = {}  # Interface name -> interface object
        self._drivers = {}  # Module name -> Model info
        self.rpc_server = None

        # Configurable instance variables
        self.rpc_port = kwargs.get('rpc_port', 6780)
        self.logger = kwargs.get('logger', logger)

        # Initialize PYTHONPATH
        self.rootPath = os.path.dirname(os.path.realpath(os.path.join(__file__, os.curdir)))
        
        if self.rootPath not in sys.path:
            sys.path.append(self.rootPath)

        # Announce Version
        self.logger.info(self.longname)
        self.logger.info("Version: %s", version.ver_full)
        self.logger.debug("Build Date: %s", version.build_date)

        #
        # Load Plugins
        #

        # Directories to search
        dirs = ['drivers', 'interfaces']
        dirs_res = map(lambda dir: os.path.join(self.rootPath, dir), dirs) + kwargs.get('plugin_dirs', [])

        # Categorize plugins by base class
        cat_filter = {
            "drivers": bases.Base_Driver,
            "interfaces": bases.Base_Interface,
            "resources": bases.Base_Resource
        }

        self.plugin_manager = common.plugin.PluginManager(directories=dirs_res, categories=cat_filter, logger=self.logger)
        self.plugin_manager.search()
        
        # Load Drivers
        self._drivers = self.plugin_manager.getPluginsByCategory('drivers')
        
        # Load Interfaces
        for interface_name in self.plugin_manager.getPluginsByCategory('interfaces'):
            self.enableInterface(interface_name)

        #
        # RPC Server
        #
        self.rpc_server = None
        self.rpc_server_thread = None

        if kwargs.get('rpc', False):
            if not self.rpc_start():
                raise RuntimeError("Unable to start RPC Server")
    
    def __del__(self):
        self.rpc_stop()

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

        # Attempt to import ptx-rpc
        try:
            import ptxrpc as rpc
        except ImportError:
            return False

        # Instantiate an rpc server
        try:
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

        except rpc.RpcServerPortInUse:
            self.logger.error("RPC Port in use, shutting down...")
            return False

        except:
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
            self._event_signal(common.constants.ManagerEvents.shutdown)

            self.rpc_server = None
            self.rpc_server_thread = None

    @staticmethod
    def getVersion():
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

    def _getInterface(self, interface_name):
        """
        Get an interface object with a given interface name. Used primarily in testing and debug, but can also be
        useful to access interface methods.

        :param interface_name: Interface plugin name or InterfaceName attribute
        :type interface_name: str
        :return:
        """
        if interface_name not in self._interfaces:
            for interf_name, interf_cls in self._interfaces.items():
                if interf_cls.info.get('interfaceName') == interface_name:
                    interface_name = interf_name

        return self._interfaces.get(interface_name)

    def getInterfaceList(self):
        """
        Get a list of interfaces that are enabled
        
        :returns: list
        """
        return self._interfaces.keys()
    
    def enableInterface(self, interface_name, **kwargs):
        """
        Enable an interface for use. Requires a class object that extends Base_Interface, NOT a class instance.

        :param interface_name: Interface plugin name
        :type interface_name: str
        :return: bool
        """
        int_cls = self.plugin_manager.getPlugin(interface_name)

        if int_cls is None:
            # Search by interface name in the plugin info
            for interf_name, interf_cls in self.plugin_manager.getPluginsByCategory('interfaces').items():
                if interf_cls.info.get('interfaceName') == interface_name:
                    interface_name = interf_name
                    int_cls = interf_cls
                    break

        if int_cls is not None:
            try:
                # Instantiate interface
                int_obj = int_cls(manager=self, logger=self.logger, **kwargs) # kwargs allows passing parameters to libs

                # If the interface is already enabled, disable the existing one
                self.disableInterface(interface_name)

                # Call the plugin hook to open the interface
                int_obj.open()

                self._interfaces[interface_name] = int_obj

                self.logger.info("Started Interface: %s" % interface_name)

                return True

            except NotImplementedError:
                return False

            except:
                self.logger.exception("Exception during interface open")
                return False
    
    def disableInterface(self, interface_name):
        """
        Disable an interface that is running.

        :param interface_name: Interface plugin name
        :return:
        """
        if interface_name in self._interfaces:
            try:
                inter = self._interfaces.pop(interface_name)

                # Call the plugin hook to close the interface
                inter.close()

                self.logger.info("Stopped Interface: %s" % interface_name)

                return True

            except NotImplementedError:
                return False
                
            except:
                self.logger.exception("Exception during interface close")
                return False
        
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
            except NotImplementedError:
                pass

            # Refresh each resource
            for resID, res in interf.getResources().items():
                try:
                    res.refresh()
                except:
                    self.logger.exception("Unhandled exception during refresh of interface: %s", interf.name)
                    raise

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

        for interface, interface_obj in self._interfaces.items():
            try:
                for uuid, res in interface_obj.resources.items():
                    ret[uuid] = res.getProperties()

                    ret[uuid].setdefault('deviceType', '')
                    ret[uuid].setdefault('deviceVendor', '')
                    ret[uuid].setdefault('deviceModel', '')
                    ret[uuid].setdefault('deviceSerial', '')
                    ret[uuid].setdefault('deviceFirmware', '')

            except NotImplementedError:
                pass
        
        return ret

    def _getResource(self, res_uuid):
        """
        Returns a resource object given the Resource UUID

        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: object
        """
        for interf in self._interfaces.values():
            try:
                temp = interf.resources.get(res_uuid)
                if temp is not None:
                    return temp

            except:
                pass
    
    def getResource(self, interface, resID):
        """
        Get a resource by name from the specified interface. Not supported by all interfaces, see interface
        documentation for more details.

        :param interface: Interface name
        :type interface: str
        :param resID: Resource Identifier
        :type resID: str
        :returns: Resource object
        """
        try:
            int_obj = self._interfaces.get(interface)
            return int_obj.getResource(resID)

        except NotImplementedError:
            pass
    
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
                matching_instruments.append(self._getResource(uuid))
                
        return matching_instruments
    
    def findInstruments(self, **kwargs):
        """
        Alias for :func:`findResources`
        """
        # NON-SERIALIZABLE
        return self.findResources(**kwargs)

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
        return self._drivers.keys()
