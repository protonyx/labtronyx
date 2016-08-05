__author__ = 'kkennedy'

import datetime
from dateutil.relativedelta import relativedelta

import labtronyx
from . import PluginController


class ScriptController(PluginController):
    def __init__(self, c_manager, model):
        super(ScriptController, self).__init__(c_manager, model)

        self._attributes = self.model.getClassAttributes()  # values
        self._parameters = self.model.getParameters()  # values

    def _handleEvent(self, event):
        # Check that the event was for us
        if len(event.args) > 0 and event.args[0] == self._uuid:
            if event.event in [labtronyx.EventCodes.script.changed]:
                self.update_properties()

            self.notifyViews(event)

    @property
    def attributes(self):
        return self._attributes

    @property
    def parameters(self):
        return self._parameters

    @property
    def results(self):
        return self.properties.get('results')

    @property
    def log(self):
        return self.model.getLog()

    def start(self):
        self.model.start()

    def stop(self):
        self.model.stop()

    def resolve_resources(self):
        self.model.resolveResources()

    def get_resource_info(self):
        return self.properties.get('resources', {})

    def assign_resource(self, attr_name, uuid):
        self.model.assignResource(attr_name, uuid)

    def human_time(self, timestamp):
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime('%x %X')

    def human_time_delta(self, delta):
        rd = relativedelta(seconds=delta)

        attrs = ['years', 'months', 'days', 'hours', 'minutes', 'seconds']
        human_readable = ['%d %s' % (getattr(rd, attr), getattr(rd, attr) > 1 and attr or attr[:-1])
                          for attr in attrs if getattr(rd, attr)]

        if len(human_readable) == 0:
            return '< 1 second'

        else:
            return ', '.join(human_readable)