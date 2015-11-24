__author__ = 'kkennedy'

import wx

import labtronyx

from ..controllers import InterfaceController
from . import FrameViewBase, PanelViewBase, DialogViewBase


class InterfaceInfoPanel(PanelViewBase):
    def __init__(self, parent, controller):
        assert(isinstance(controller, InterfaceController))
        super(InterfaceInfoPanel, self).__init__(parent, controller, id=wx.ID_ANY)

        self.mainSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        self._fields = {}
        self.props = {}

        # Controls
        self._createField("Interface Name", "interfaceName")

        self.btn_refresh = wx.Button(self, -1, "Refresh")
        self.btn_open = wx.Button(self, -1, "Open Resource")

        self.mainSizer.Add((10, 10))
        self.mainSizer.Add(self.btn_refresh, 0, wx.ALIGN_LEFT)
        self.mainSizer.Add((10, 10))
        self.mainSizer.Add(self.btn_open, 0, wx.ALIGN_LEFT)

        self.Bind(wx.EVT_BUTTON, self.e_OnClickRefresh, self.btn_refresh)
        self.Bind(wx.EVT_BUTTON, self.e_OnClickOpen, self.btn_open)

        self.mainSizer.AddGrowableCol(1)

        self.SetSizer(self.mainSizer)
        self.SetAutoLayout(True)

        self.updateFields()

    def _handleEvent(self, event):
        if event.event in [labtronyx.EventCodes.interface.changed]:
            self.updateFields()

    def _createField(self, label, prop_key):
        lblNew = wx.StaticText(self, -1, label + ":")
        self._fields[prop_key] = wx.StaticText(self, -1, "")

        self.mainSizer.Add(lblNew,                 0, wx.ALIGN_RIGHT|wx.RIGHT, 5)
        self.mainSizer.Add(self._fields[prop_key], 1, wx.ALIGN_LEFT|wx.EXPAND)

    def updateFields(self):
        self.props = self.controller.properties

        for prop_key, field in self._fields.items():
            field.SetLabelText(self.props.get(prop_key, ''))

        # Refresh panel since item lengths may have changed
        self.mainSizer.Fit(self)
        self.Fit()

    def e_OnClickRefresh(self, event):
        self.controller.refresh()

    def e_OnClickOpen(self, event):
        pass


class InterfaceOpenResourceDialog(DialogViewBase):
    pass