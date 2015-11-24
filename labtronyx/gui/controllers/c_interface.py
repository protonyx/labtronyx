__author__ = 'kkennedy'

import labtronyx
from .c_base import PluginController


class InterfaceController(PluginController):
    def __init__(self, c_manager, model):
        super(InterfaceController, self).__init__(c_manager, model)

    def refresh(self):
        self.model.refresh()