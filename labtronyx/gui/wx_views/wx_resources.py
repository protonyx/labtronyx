__author__ = 'kkennedy'

import wx
import wx.lib.sized_controls

import labtronyx

from ..controllers import ResourceController
from . import FrameViewBase, PanelViewBase, DialogViewBase


class ResourceInfoPanel(PanelViewBase):
    def __init__(self, parent, controller):
        assert(isinstance(controller, ResourceController))
        super(ResourceInfoPanel, self).__init__(parent, controller, id=wx.ID_ANY)

        self._fields = {}

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.topSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.leftSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        self._createField("Resource ID", "resourceID")
        self._createField("Interface", "interfaceName")
        self._createField("Resource Type", "resourceType")
        self._createField("Device Type", "deviceType")
        self._createField("Driver", "driver")

        self.rightSizer = wx.BoxSizer(wx.VERTICAL)
        self.lst_methods = wx.ListBox(self, -1, style=wx.LB_SINGLE)
        self.rightSizer.Add(wx.StaticText(self, -1, 'Methods', style=wx.ALIGN_CENTER),
                            0, wx.ALIGN_CENTER | wx.EXPAND | wx.BOTTOM, 5)
        self.rightSizer.Add(self.lst_methods, 0, wx.EXPAND)

        self.btn_driver = wx.Button(self, -1, "Driver")
        self.leftSizer.Add((10, 10))
        self.leftSizer.Add(self.btn_driver, 0, wx.ALIGN_LEFT)
        self.Bind(wx.EVT_BUTTON, self.e_DriverOnClick, self.btn_driver)

        self.leftSizer.AddGrowableCol(1)

        self.topSizer.Add(self.leftSizer, 1, wx.ALIGN_LEFT | wx.EXPAND)
        self.topSizer.Add(self.rightSizer, 1, wx.ALIGN_RIGHT | wx.EXPAND)
        self.mainSizer.Add(self.topSizer, 0, wx.EXPAND)

        self.SetSizer(self.mainSizer)
        self.SetAutoLayout(True)

        self.updateFields()

    def _handleEvent(self, event):
        if event.event in [labtronyx.EventCodes.resource.driver_loaded,
                           labtronyx.EventCodes.resource.driver_unloaded,
                           labtronyx.EventCodes.resource.changed]:
            self.updateFields()

    def _createField(self, label, prop_key):
        lblNew = wx.StaticText(self, -1, label + ":")
        self._fields[prop_key] = wx.StaticText(self, -1, "")

        self.leftSizer.Add(lblNew, 0, wx.ALIGN_RIGHT | wx.RIGHT, 5)
        self.leftSizer.Add(self._fields[prop_key], 1, wx.ALIGN_LEFT | wx.EXPAND)

    def updateFields(self):
        props = self.controller.properties

        for prop_key, field in self._fields.items():
            field.SetLabelText(props.get(prop_key, ''))

        if props.get('driver', '') == '':
            self.btn_driver.SetLabelText("Load Driver")

        else:
            self.btn_driver.SetLabelText("Unload Driver")

        # Refresh panel since item lengths may have changed
        self.leftSizer.Fit(self)

        methods = self.controller.get_methods()

        self.lst_methods.Clear()
        self.lst_methods.AppendItems(methods)

        self.Fit()

    def e_DriverOnClick(self, event):
        if self.controller.properties.get('driver', '') == '':
            # Open load driver panel as a dialogue
            drv_dlg = DriverLoadDialog(self, self.controller)
            # drv_dlg.CenterOnScreen()

            val = drv_dlg.ShowModal()

            if val == wx.ID_OK:
                driver = drv_dlg.getSelectedDriver()

                if driver != '':
                    self.controller.load_driver(driver)

                else:
                    msg = wx.MessageDialog(self, 'No driver was selected', 'Load driver error', wx.OK|wx.ICON_ERROR)
                    msg.ShowModal()
                    msg.Destroy()

        else:
            self.controller.unload_driver()


class DriverLoadDialog(DialogViewBase):
    def __init__(self, parent, controller):
        assert (isinstance(controller, ResourceController))
        super(DriverLoadDialog, self).__init__(parent, controller, id=wx.ID_ANY, title="Resource %s" % controller.resID)

        lbl = wx.StaticText(self, -1, "Load Driver")
        lbl.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))

        self.drv_select = DriverSelectorPanel(self, controller)
        btnOk = wx.Button(self, wx.ID_OK, "&Ok")
        btnOk.SetDefault()
        btnCancel = wx.Button(self, wx.ID_CANCEL, "&Cancel")

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(btnOk)
        btnSizer.AddButton(btnCancel)
        btnSizer.Realize()

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(lbl,                 0, wx.EXPAND|wx.ALL, border=5)
        mainSizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, border=5)
        mainSizer.Add(self.drv_select,     0, wx.EXPAND|wx.ALL, border=5)
        mainSizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, border=5)
        mainSizer.Add(btnSizer,            0, wx.ALL|wx.ALIGN_RIGHT, border=5)

        self.SetSizer(mainSizer)
        mainSizer.Fit(self)

    def getSelectedDriver(self):
        return self.drv_select.getSelectedDriver()


class DriverSelectorPanel(PanelViewBase):
    """
    Driver Selection Widget

    :param controller:  Resource controller
    :type controller:   controllers.resource.ResourceController
    """
    def __init__(self, parent, controller):
        assert (isinstance(controller, ResourceController))
        super(DriverSelectorPanel, self).__init__(parent, controller, id=wx.ID_ANY, style=wx.WANTS_CHARS)

        vendors = self.controller.manager.list_driver_vendors()
        vendors.sort()
        vendors = ["Any"] + vendors

        self.panel_form = wx.lib.sized_controls.SizedPanel(self, -1)
        self.panel_form.SetSizerType("form")

        wx.StaticText(self.panel_form, -1, "Vendor")
        self.w_vendor = wx.Choice(self.panel_form, -1, size=(200, -1), choices=vendors)
        self.w_vendor.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.OnVendorChange, self.w_vendor)

        wx.StaticText(self.panel_form, -1, "Model")
        self.w_model = wx.Choice(self.panel_form, -1, size=(200, -1), choices=[])
        self.Bind(wx.EVT_CHOICE, self.OnModelChange, self.w_model)

        wx.StaticText(self.panel_form, -1, "Driver")
        self.w_driver = wx.Choice(self.panel_form, -1, size=(200, -1), choices=[])

        self.updateModels()
        self.updateDrivers()

        self.panel_form.Fit()
        self.SetSize(self.panel_form.GetSize())

    def getSelectedDriver(self):
        return self.w_driver.GetStringSelection()

    def OnVendorChange(self, event):
        self.updateModels()
        self.updateDrivers()

    def OnModelChange(self, event):
        self.updateDrivers()

    def updateModels(self):
        if self.w_vendor.GetSelection() == 0:
            models = ["Any"]

        else:
            vendor = self.w_vendor.GetStringSelection()

            models = self.controller.manager.list_driver_models_from_vendor(vendor)
            models.sort()

            models = ["Any"] + models

        self.w_model.Clear()
        self.w_model.AppendItems(models)
        self.w_model.SetSelection(0)

    def updateDrivers(self):
        vend_sel = self.w_vendor.GetSelection()
        vendor = self.w_vendor.GetStringSelection()
        mod_sel = self.w_model.GetSelection()
        model = self.w_model.GetStringSelection()

        if vend_sel == 0 and mod_sel == 0:
            drivers = self.controller.manager.get_drivers()

        elif mod_sel == 0:
            drivers = self.controller.manager.get_drivers_from_vendor(vendor)

        else:
            drivers = self.controller.manager.get_drivers_from_vendor_model(vendor, model)

        interfaceName = self.controller.properties.get('interface', '')
        drivers = self.controller.manager.filter_compatible_drivers(drivers, interfaceName)
        driver_list = sorted(drivers.keys())

        self.w_driver.Clear()
        self.w_driver.AppendItems(driver_list)