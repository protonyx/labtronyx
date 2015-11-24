import logging


class BaseController(object):
    def __init__(self):
        self._views = []

        self.__logger = logging.getLogger('labtronyx-gui')

    def registerView(self, view_obj):
        self._views.append(view_obj)

    def unregisterView(self, view_obj):
        self._views.remove(view_obj)

    def notifyViews(self, event):
        for v in self._views:
            try:
                v.handleEvent(event)

            except Exception as e:
                pass

    def _handleEvent(self, event):
        pass

    @property
    def logger(self):
        return self.__logger


class PluginController(BaseController):
    def __init__(self, c_manager, model):
        super(PluginController, self).__init__()
        self._manager = c_manager
        self._model = model

        # Cache properties
        self._properties = {}
        self.update_properties()

        self._uuid = self._properties.get('uuid')
        self._fqn = self._properties.get('fqn')

    def update_properties(self):
        self._properties = self._model.getProperties()

    @property
    def model(self):
        return self._model

    @property
    def manager(self):
        return self._manager

    @property
    def uuid(self):
        return self._uuid

    @property
    def fqn(self):
        return self._fqn

    @property
    def properties(self):
        return self._properties