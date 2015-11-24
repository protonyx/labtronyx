__author__ = 'kkennedy'

import labtronyx
from . import PluginController


class ResourceController(PluginController):
    """
    Wraps RemoteResource
    """

    def __init__(self, c_manager, model):
        super(ResourceController, self).__init__(c_manager, model)

        self._resID = self._properties.get('resourceID')

    def _handleEvent(self, event):
        # Check that the event was for us
        if len(event.args) > 0 and event.args[0] == self._uuid:
            if event.event in [labtronyx.EventCodes.resource.driver_loaded,
                               labtronyx.EventCodes.resource.driver_unloaded,
                               labtronyx.EventCodes.resource.changed]:
                self.update_properties()

            self.notifyViews(event)

    @property
    def resID(self):
        return self._resID

    @property
    def driver(self):
        return self.properties.get('driver')

    def get_methods(self):
        return self.model._getMethods()

    def load_driver(self, new_driver):
        return self._model.loadDriver(new_driver)

    def unload_driver(self):
        return self._model.unloadDriver()