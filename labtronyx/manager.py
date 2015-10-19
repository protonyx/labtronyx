
# System Imports
import os, sys
import socket
import threading

# Local Imports
from . import logger

from . import bases
from . import common

from .common import *
from .common.errors import *

from . import version


class InstrumentManager(object):
    """
    Labtronyx InstrumentManager

    Facilitates communication with instruments using all available interfaces.

    :param rpc:         Enable RPC endpoint
    :type rpc:          bool
    :param rpc_port:    RPC endpoint port
    :type rpc_port:     int
    :param plugin_dirs: List of directories containing plugins
    :type plugin_dirs:  list
    :param logger:      Logger instance if you wish to override the internal instance
    :type logger:       Logging.logger object
    """
    name = 'Labtronyx'
    longname = 'Labtronyx Instrumentation Control Framework'
    
    def __init__(self, **kwargs):
        # Initialize instance variables
        self._interfaces = {}  # Interface name -> interface object
        self._drivers = {}  # Module name -> Model info

        # Configurable instance variables
        self.logger = kwargs.get('logger', logger)

        # Initialize PYTHONPATH
        self.rootPath = os.path.dirname(os.path.realpath(os.path.join(__file__, os.curdir)))
        if self.rootPath not in sys.path:
            sys.path.append(self.rootPath)

        # Announce Version
        self.logger.info(self.longname)
        self.logger.info("Version: %s", version.ver_full)
        self.logger.debug("Build Date: %s", version.build_date)

        # Directories to search for plugins
        dirs = ['drivers', 'interfaces']
        dirs_res = [os.path.join(self.rootPath, dir) for dir in dirs] + kwargs.get('plugin_dirs', [])

        # Categorize plugins by base class
        cat_filter = {
            "drivers": bases.Base_Driver,
            "interfaces": bases.Base_Interface,
            "resources": bases.Base_Resource
        }

        # Load Plugins
        self.plugin_manager = plugin.PluginManager(directories=dirs_res, categories=cat_filter, logger=self.logger)
        self.plugin_manager.search()
        
        # Load Drivers
        self._drivers = self.plugin_manager.getPluginsByCategory('drivers')
        
        # Load Interfaces
        for interface_name in self.plugin_manager.getPluginsByCategory('interfaces'):
            self.enableInterface(interface_name)

        #
        # Server
        #
        self._server = None
        self._server_port = kwargs.get('server_port', 6780)

        if kwargs.get('server', False):
            if not self.server_start():
                raise RuntimeError("Unable to start Labtronyx Server")
    
    def __del__(self):
        try:
            self.server_stop()
        except:
            pass

        self._close()

    def _close(self):
        """
        Close all resources and interfaces
        """
        # Disable all interfaces, close all resources
        for interface_name in self._interfaces.values(): # use values() so a copy is created
            self.disableInterface(interface_name)

    #===========================================================================
    # Labtronyx Server
    #===========================================================================

    def server_start(self, new_thread=True):
        """
        Start the RPC Server and being listening for remote connections.

        :returns: True if successful, False otherwise
        """
        # Clean out old RPC server, if any exists
        self.server_stop()

        from werkzeug.serving import run_simple

        # Create a server app
        self._server = common.server.create_server(self, self._server_port, logger=self.logger)

        srv_start_cmd = lambda: run_simple(
            hostname='localhost', port=self._server_port, application=self._server,
            threaded=True, use_debugger=True
        )

        # Instantiate an rpc server
        if new_thread:
            import threading

            server_thread = threading.Thread(name='Labtronyx-Server', target=srv_start_cmd)
            server_thread.start()

            return True

        else:
            srv_start_cmd()

    def server_stop(self):
        """
        Stop the Server
        """
        if self._server is not None:
            try:
                # Must use the REST API to shutdown
                import urllib2
                url = 'http://{0}:{1}/api/shutdown'.format('localhost', self._server_port)
                resp = urllib2.Request(url)
                handler = urllib2.urlopen(resp)

                if handler.code == 200:
                    self.logger.debug('Server stopped')
                else:
                    self.logger.error('Server stop returned code: %d', handler.code)

                # Signal the event
                self._event_signal(constants.ManagerEvents.shutdown)

                self._server = None

            except:
                pass

    @property
    def version(self):
        return version

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

        :returns: str
        """
        return socket.gethostbyname(self.getHostname())
    
    def getHostname(self):
        """
        Get the local hostname

        :returns: str
        """
        return socket.gethostname()

    #===========================================================================
    # Event Processing and Dispatch
    #===========================================================================

    def _event_signal(self, event, **kwargs):
        """
        Private method called internally to signal events. Calls handlers and dispatches event signal to subscribed
        clients

        :param event:   event object
        :param kwargs:  arguments
        """
        pass

    # ===========================================================================
    # Interface Operations
    # ===========================================================================

    @property
    def interfaces(self):
        return self._interfaces

    def _getInterface(self, interface_name):
        """
        Get an interface object with a given interface name. Used primarily in testing and debug, but can also be
        useful to access interface methods.

        :param interface_name:  Interface plugin name or InterfaceName attribute
        :type interface_name:   str
        :return:                object
        """
         # NON-SERIALIZABLE
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

        :param interface_name:  Interface plugin name
        :type interface_name:   str
        :returns:               bool
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
                # If the interface is already enabled, disable the existing one
                self.disableInterface(interface_name)

                # Instantiate interface
                int_obj = int_cls(manager=self, logger=self.logger, **kwargs) # kwargs allows passing parameters to libs

                # Call the plugin hook to open the interface. Ensure interface opens correctly
                if int_obj.open():
                    self._interfaces[interface_name] = int_obj

                    self.logger.info("Started Interface: %s", interface_name)
                    return True

                else:
                    self.logger.error("Interface %s failed to open", interface_name)
                    return False

            except NotImplementedError:
                return False

            except:
                self.logger.exception("Exception during interface open")
                return False
    
    def disableInterface(self, interface_name):
        """
        Disable an interface that is running.

        :param interface_name:  Interface plugin name
        :returns:               bool
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
        
    # ===========================================================================
    # Resource Operations
    # ===========================================================================
    
    def refresh(self):
        """
        Refresh all interfaces and resources. Attempts enumeration on all interfaces, then calls the `refresh`
        method for all resources.

        :returns: bool
        """
        for interf in self._interfaces.values():
            try:
                # Discover any new resources
                interf.refresh()
            except NotImplementedError:
                pass

            # Refresh each resource
            for resID, res in interf.resources.items():
                try:
                    res.refresh()
                except NotImplementedError:
                    pass
                except:
                    self.logger.exception("Unhandled exception during refresh of interface: %s", interf.name)
                    raise
            
        return True
    
    def getProperties(self):
        """
        Returns the property dictionaries for all resources
        
        :returns: dict
        """
        ret = {}

        for interface, interface_obj in self._interfaces.items():
            try:
                for resID, res in interface_obj.resources.items():
                    props = res.getProperties()

                    # UUID is not used to key properties within the interface
                    uuid = props.get('uuid', res.uuid)

                    ret[uuid] = props
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

        :param res_uuid:        Unique Resource Identifier (UUID)
        :type res_uuid:         str
        :returns:               object
        :raises:                KeyError if resource is not found
        """
         # NON-SERIALIZABLE
        for interf in self._interfaces.values():
            for resID, res in interf.resources.items():
                if res.uuid == res_uuid:
                    return res

        raise KeyError('Resource not found')
    
    def getResource(self, interface, resID, driverName=None):
        """
        Get a resource by name from the specified interface. Not supported by all interfaces, see interface
        documentation for more details.

        :param interface:       Interface name
        :type interface:        str
        :param resID:           Resource Identifier
        :type resID:            str
        :param driverName:      Driver to load for resource
        :type driverName:       str
        :returns:               Resource object
        :raises:                InterfaceUnavailable
        :raises:                ResourceUnavailable
        :raises:                InterfaceError
        """
         # NON-SERIALIZABLE
        int_obj = self._getInterface(interface)

        if int_obj is None:
            raise InterfaceUnavailable('Interface not found')

        try:
            # Call the interface getResource hook
            res = int_obj.getResource(resID)

            # Attempt to load the specified driver, but do not force
            res.loadDriver(driverName)

            return res

        except NotImplementedError:
            raise InterfaceError('Operation not support by interface %s' % interface)
    
    def findResources(self, **kwargs):
        """
        Get a list of resources/instruments that match the parameters specified.
        Parameters can be any key found in the resource property dictionary, such as these:

        :param uuid:            Unique Resource Identifier (UUID)
        :param interface:       Interface
        :param resourceID:      Interface Resource Identifier (Port, Address, etc.)
        :param resourceType:    Resource Type (Serial, VISA, etc.)
        :param deviceVendor:    Instrument Vendor
        :param deviceModel:     Instrument Model Number
        :param deviceSerial:    Instrument Serial Number
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
                try:
                    matching_instruments.append(self._getResource(uuid))
                except KeyError:
                    pass
                
        return matching_instruments
    
    def findInstruments(self, **kwargs):
        """
        Alias for :func:`findResources`
        """
        # NON-SERIALIZABLE
        return self.findResources(**kwargs)

    # ===========================================================================
    # Driver Operations
    # ===========================================================================

    @property
    def drivers(self):
        return self._drivers
                
    def getDrivers(self):
        """
        Get a list of loaded drivers

        :return: list
        """
        return self._drivers.keys()
