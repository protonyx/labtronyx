__author__ = 'kkennedy'

import labtronyx
from . import BaseController, InterfaceController, ResourceController, ScriptController

rpc_controllers = {
    'resource': ResourceController,
    'script': ScriptController
}


class ManagerController(BaseController):
    """
    Wraps RemoteManager
    """

    def __init__(self, model):
        BaseController.__init__(self)

        self._model = model

        self._hostname = self._model.getHostname()

        # Dictionary caches
        self._properties = {}
        self._attributes = {}

        # Controller objects
        self._resources = {}
        self._interfaces = {}
        self._scripts = {}

        self.refresh()

    @property
    def model(self):
        return self._model

    @property
    def hostname(self):
        return self._hostname

    def _handleEvent(self, event):

        # Check if this event is for us
        if event.hostname == self._hostname:
            if event.event in [labtronyx.EventCodes.resource.created,
                               labtronyx.EventCodes.resource.destroyed]:
                self.refresh()

            elif event.event in [labtronyx.EventCodes.interface.created,
                                 labtronyx.EventCodes.interface.destroyed]:
                self.refresh()

            elif event.event in [labtronyx.EventCodes.script.created,
                                 labtronyx.EventCodes.script.destroyed]:
                self.refresh()

            # Notify resource controllers
            for res_uuid, res_con in self._resources.items():
                res_con._handleEvent(event)

            # Notify interface controllers
            for int_uuid, int_con in self._interfaces.items():
                int_con._handleEvent(event)

            # Notify script controllers
            for scr_uuid, scr_con in self._scripts.items():
                scr_con._handleEvent(event)

            self.notifyViews(event)

    def refresh(self):
        self.model.refresh()

        self._properties = self.model.getProperties()
        self._attributes = self.model.getAttributes()

        # Create controllers for each of the plugins
        for res_uuid, resObj in self.model.resources.items():
            if res_uuid not in self._resources:
                remote = ResourceController(self, resObj)
                self._resources[res_uuid] = remote

        for scr_uuid, scrObj in self.model.scripts.items():
            if scr_uuid not in self._scripts:
                remote = ScriptController(self, scrObj)
                self._scripts[scr_uuid] = remote

        for int_uuid, intObj in self.model.interfaces.items():
            if int_uuid not in self._interfaces:
                remote = InterfaceController(self, intObj)
                self._interfaces[int_uuid] = remote

    def get_resource(self, res_uuid):
        return self._resources.get(res_uuid)

    @property
    def resources(self):
        return self._resources

    @property
    def resource_classes(self):
        return {fqn: plug_attrs for fqn, plug_attrs in self.attributes.items()
                if plug_attrs.get('pluginType') == 'resource'}

    def get_script(self, scr_uuid):
        return self._scripts.get(scr_uuid)

    @property
    def scripts(self):
        return self._scripts

    @property
    def script_classes(self):
        return {fqn: plug_attrs for fqn, plug_attrs in self.attributes.items()
                if plug_attrs.get('pluginType') == 'script'}

    def get_interface(self, int_uuid):
        return self._interfaces.get(int_uuid)

    @property
    def interfaces(self):
        return self._interfaces

    @property
    def interface_classes(self):
        return {fqn: plug_attrs for fqn, plug_attrs in self.attributes.items()
                if plug_attrs.get('pluginType') == 'interface'}

    @property
    def properties(self):
        return self._properties

    @property
    def attributes(self):
        return self._attributes

    @property
    def driver_classes(self):
        return {fqn: plug_attrs for fqn, plug_attrs in self.attributes.items()
                if plug_attrs.get('pluginType') == 'driver'}

    def list_drivers(self):
        return self.driver_classes.keys()

    def list_driver_vendors(self):
        vendors = set()

        for driver_name, driver_info in self.driver_classes.items():
            for comp_vendor, comp_models in driver_info.get('compatibleInstruments', {}).items():
                vendors.add(comp_vendor)

        return list(vendors)

    def list_driver_models_from_vendor(self, vendor):
        models = set()

        for driver_name, driver_info in self.driver_classes.items():
            for comp_vendor, comp_models in driver_info.get('compatibleInstruments', {}).items():
                if vendor == comp_vendor:
                    models.update(comp_models)

        return list(models)

    def get_drivers(self):
        return self.driver_classes

    def get_drivers_from_vendor(self, vendor):
        drivers = {}

        for driver_name, driver_info in self.driver_classes.items():
            for comp_vendor, comp_models in driver_info.get('compatibleInstruments', {}).items():
                if vendor == comp_vendor:
                    drivers[driver_name] = driver_info

        return drivers

    def get_drivers_from_vendor_model(self, vendor, model):
        drivers = {}

        for driver_name, driver_info in self.driver_classes.items():
            for comp_vendor, comp_models in driver_info.get('compatibleInstruments', {}).items():
                if vendor == comp_vendor and model in comp_models:
                    drivers[driver_name] = driver_info

        return drivers

    def filter_compatible_drivers(self, drivers, interfaceName):
        return {k:v for k,v in drivers.items() if interfaceName in v.get('compatibleInterfaces', [])}

    def list_resources(self):
        return self._resources.keys()

    def get_script_class_attributes(self, script_fqn):
        pass

    def get_script_attributes(self):
        return {plug_uuid: plug_attr for plug_uuid, plug_attr in self.attributes.items()
                                     if plug_attr.get('pluginType') == 'script'}

    def create_script_instance(self, fqn, **kwargs):
        new_uuid = self.model.openScript(fqn, **kwargs)

        return new_uuid

    def destroy_script_instance(self, uuid):
        return self.model.closeScript(uuid)