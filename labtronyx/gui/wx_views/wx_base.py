import logging

import wx


class WxViewBase(object):
    def __init__(self, controller=None):
        self.__controller = controller

        self.__logger = logging.getLogger('labtronyx-gui')

        if self.controller is not None:
            self.__controller.registerView(self)

    def __del__(self):
        if self.controller is not None:
            self.__controller.unregisterView(self)

    @property
    def logger(self):
        return self.__logger

    @property
    def controller(self):
        return self.__controller

    def handleEvent(self, event):
        """
        Handle an event and pass it into the wx Application. Do not override
        :param event:
        """
        wx.CallAfter(self._handleEvent, event)

    def _handleEvent(self, event):
        """
        Override this method to handle events from within the GUI mainloop

        :param event:
        """
        pass


class FrameViewBase(wx.Frame, WxViewBase):
    def __init__(self, parent, controller, **kwargs):
        wx.Frame.__init__(self, parent=parent, **kwargs)
        WxViewBase.__init__(self, controller)


class PanelViewBase(wx.Panel, WxViewBase):
    def __init__(self, parent, controller, **kwargs):
        wx.Panel.__init__(self, parent=parent, **kwargs)
        WxViewBase.__init__(self, controller)


class DialogViewBase(wx.Dialog, WxViewBase):
    def __init__(self, parent, controller, **kwargs):
        wx.Dialog.__init__(self, parent=parent, **kwargs)
        WxViewBase.__init__(self, controller)