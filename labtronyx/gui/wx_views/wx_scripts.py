import sys
import wx
from wx.lib import scrolledpanel

import labtronyx

from ..controllers import ScriptController
from . import FrameViewBase, PanelViewBase, DialogViewBase


class ScriptInfoPanel(PanelViewBase):
    def __init__(self, parent, controller):
        assert(isinstance(controller, ScriptController))
        super(ScriptInfoPanel, self).__init__(parent, controller, id=wx.ID_ANY)

        self.props = self.controller.properties

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.attr_sizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)

        # Top section
        # self._fieldAttributes("Script UUID", "uuid")
        self._fieldAttributes("Script Name", "name")
        self._fieldAttributes("Description", "description")
        self._fieldAttributes("Category", "category")

        self.attr_sizer.Add(wx.StaticText(self, -1, "State:"), 0, wx.ALIGN_RIGHT | wx.RIGHT, 5)
        self.txt_state = wx.StaticText(self, -1, "")
        self.attr_sizer.Add(self.txt_state, 0, wx.ALIGN_LEFT)
        self.attr_sizer.Add((10, 10))
        self.btn_do = wx.Button(self, -1, "")
        self.attr_sizer.Add(self.btn_do, 0, wx.ALIGN_LEFT)
        self.Bind(wx.EVT_BUTTON, self.e_OnButton, self.btn_do)

        self.attr_sizer.AddGrowableCol(1)

        # Lower section
        self.notebook = wx.Notebook(self, -1, style=wx.BK_DEFAULT)
        # Parameters
        self.nb_parameters = ScriptParametersPanel(self.notebook, self.controller)
        self.notebook.AddPage(self.nb_parameters, "Parameters")
        # Resources
        self.nb_resources = ScriptResourcesPanel(self.notebook, self.controller)
        self.notebook.AddPage(self.nb_resources, "Resources")
        # Status/Log
        self.nb_status = ScriptStatusPanel(self.notebook, self.controller)
        self.notebook.AddPage(self.nb_status, "Status")
        # Results
        self.nb_results = ScriptResultsPanel(self.notebook, self.controller)
        self.notebook.AddPage(self.nb_results, "Results")

        self.mainSizer.Add(self.attr_sizer, 0, wx.EXPAND)
        self.mainSizer.Add(self.notebook, 1, wx.EXPAND | wx.TOP, 10)

        self.SetSizer(self.mainSizer)
        self.SetAutoLayout(True)
        self.mainSizer.Fit(self)
        self.Fit()

        self.update()

    def _handleEvent(self, event):
        if event.event in [labtronyx.EventCodes.script.changed]:
            self.update()

    def update(self):
        properties = self.controller.properties
        results = properties.get('results', [])

        if properties.get('running', False):
            self.btn_do.SetLabelText('Stop')
        else:
            self.btn_do.SetLabelText('Start')

        if properties.get('running', False):
            self.txt_state.SetLabelText('Running')
            self.txt_state.SetForegroundColour(wx.YELLOW)

        elif len(results) > 0:
            last_result = results[-1].get('result', '')
            if last_result == labtronyx.ScriptResult.PASS:
                self.txt_state.SetLabelText('PASS')
                self.txt_state.SetForegroundColour(wx.GREEN)

            elif last_result == labtronyx.ScriptResult.FAIL:
                self.txt_state.SetLabelText('FAIL')
                self.txt_state.SetForegroundColour(wx.RED)

            elif last_result == labtronyx.ScriptResult.STOPPED:
                self.txt_state.SetLabelText('STOPPED')
                self.txt_state.SetForegroundColour(wx.RED)

        elif properties.get('ready', False):
            self.txt_state.SetLabelText('Ready')
            self.txt_state.SetForegroundColour(wx.BLACK)

    def _fieldAttributes(self, label, attr_key):
        lblNew = wx.StaticText(self, -1, label + ":")
        value = self.props.get(attr_key) or ''
        txtNew = wx.StaticText(self, -1, value)

        self.attr_sizer.Add(lblNew, 0, wx.ALIGN_RIGHT | wx.RIGHT, 5)
        self.attr_sizer.Add(txtNew, 1, wx.ALIGN_LEFT | wx.EXPAND)

    def e_OnButton(self, event):
        properties = self.controller.properties
        if properties.get('running', False):
            self.controller.stop()
        else:
            self.controller.start()


class ScriptParametersPanel(PanelViewBase):
    def __init__(self, parent, controller):
        assert(isinstance(controller, ScriptController))
        super(ScriptParametersPanel, self).__init__(parent, controller, id=wx.ID_ANY)

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.sp = scrolledpanel.ScrolledPanel(self)

        self.param_info = self.controller.attributes.get('parameters')
        self.params = self.controller.parameters

        self.paramSizer = wx.BoxSizer(wx.VERTICAL)

        if len(self.param_info) == 0:
            self.paramSizer.Add(wx.StaticText(self.sp, -1, 'No parameters'), 0)

        for param, param_details in self.param_info.items():
            self._fieldParameters(param)
            self.paramSizer.Add(wx.StaticLine(self.sp, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.ALL, 5)

        self.sp.SetSizer(self.paramSizer)
        self.sp.SetAutoLayout(True)
        self.sp.SetupScrolling()

        self.mainSizer.Add(self.sp, 1, wx.EXPAND)
        self.SetSizer(self.mainSizer)

    def _fieldParameters(self, param_attr):
        param_info = self.param_info.get(param_attr)

        fieldSizer = wx.BoxSizer(wx.HORIZONTAL)
        lbl_attr = wx.StaticText(self.sp, -1, param_attr)
        lbl_attr.Wrap(200)
        lbl_desc = wx.StaticText(self.sp, -1, param_info.get('description'))
        lbl_desc.SetFont(wx.Font(8, wx.DEFAULT, wx.ITALIC, wx.NORMAL))
        lbl_desc.Wrap(200)
        txt_val = wx.StaticText(self.sp, -1, self.params.get(param_attr), style=wx.ALIGN_RIGHT)
        txt_val.Wrap(200)

        descSizer = wx.BoxSizer(wx.VERTICAL)
        descSizer.Add(lbl_attr, 0)
        descSizer.Add(lbl_desc, 0)
        fieldSizer.Add(descSizer, 1, wx.ALIGN_LEFT | wx.EXPAND)
        fieldSizer.Add(txt_val, 1, wx.ALIGN_RIGHT | wx.EXPAND)
        self.paramSizer.Add(fieldSizer, 0, wx.EXPAND | wx.ALL, 5)


class ScriptResourcesPanel(PanelViewBase):
    def __init__(self, parent, controller):
        assert(isinstance(controller, ScriptController))
        super(ScriptResourcesPanel, self).__init__(parent, controller, id=wx.ID_ANY)

        self.spSizer = wx.BoxSizer(wx.VERTICAL)
        self.sp = scrolledpanel.ScrolledPanel(self)

        res_info = self.controller.get_resource_info()
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.btn_reset = wx.Button(self.sp, -1, "Reset")
        self.Bind(wx.EVT_BUTTON, self.e_OnClick, self.btn_reset)

        self.mainSizer.Add(self.btn_reset, 0, wx.ALL, 5)

        for attr_name, res_list in res_info.items():
            res_ctrl = ScriptResourceSelector(self.sp, self.controller, attr_name)
            self.mainSizer.Add(wx.StaticLine(self.sp, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.ALL, 5)
            self.mainSizer.Add(res_ctrl, 0, wx.EXPAND | wx.ALL, 5)

        self.sp.SetAutoLayout(True)
        self.sp.SetupScrolling()
        self.sp.SetSizer(self.mainSizer)

        self.spSizer.Add(self.sp, 1, wx.EXPAND)
        self.SetSizer(self.spSizer)

    def e_OnClick(self, event):
        self.controller.resolve_resources()


class ScriptResourceSelector(PanelViewBase):
    def __init__(self, parent, controller, attr_name):
        assert(isinstance(controller, ScriptController))
        super(ScriptResourceSelector, self).__init__(parent, controller, id=wx.ID_ANY)

        self.attr_name = attr_name
        self.res_cons = []

        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.attrSizer = wx.BoxSizer(wx.VERTICAL)

        self.txt_attr = wx.StaticText(self, -1, "Resource Attribute: %s" % attr_name)
        self.txt_res = wx.StaticText(self, -1, '')
        self.res_picker = wx.Choice(self, -1)
        self.btn = wx.Button(self, -1, 'Use')
        self.Bind(wx.EVT_BUTTON, self.e_OnClick, self.btn)

        self.attrSizer.Add(self.txt_attr, 0, wx.ALIGN_LEFT)
        self.attrSizer.Add(self.txt_res, 0, wx.ALIGN_LEFT)
        self.mainSizer.Add(self.attrSizer, 1)
        self.mainSizer.Add(self.res_picker, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.mainSizer.Add(self.btn, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
        self.SetSizer(self.mainSizer)

        self.update()

    def _handleEvent(self, event):
        if event.event in [labtronyx.EventCodes.script.changed]:
            self.update()

    def update(self):
        self.res_picker.Clear()

        res_info = self.controller.get_resource_info().get(self.attr_name, [])

        self.res_cons = [self.controller.manager.get_resource(uuid)
                             for uuid in res_info]

        for res_cont in self.res_cons:
            if res_cont.driver is not None:
                txt_display = res_cont.properties.get('deviceVendor', '') + ' ' + \
                              res_cont.properties.get('deviceModel', '')

            else:
                txt_display = res_cont.resID

            self.res_picker.Append(txt_display)

        if len(res_info) == 1:
            # Resolved
            self.btn.Disable()
            self.res_picker.SetSelection(0)
            self.res_picker.Disable()

        else:
            # Not resolved
            self.btn.Enable()
            self.res_picker.Enable()

    def e_OnClick(self, event):
        sel_res = self.res_picker.GetCurrentSelection()

        sel_res_uuid = self.res_cons[sel_res]
        self.controller.assign_resource(self.attr_name, sel_res_uuid)


class ScriptStatusPanel(PanelViewBase):
    def __init__(self, parent, controller):
        assert(isinstance(controller, ScriptController))
        super(ScriptStatusPanel, self).__init__(parent, controller, id=wx.ID_ANY)

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.topSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.status = wx.StaticText(self, -1)
        self.progress = wx.Gauge(self, -1, size=(-1, 25))
        self.log = wx.TextCtrl(self, -1, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)

        self.topSizer.Add(self.status, 2, wx.RIGHT, 10)
        self.topSizer.Add(self.progress, 1)

        self.mainSizer.Add(self.topSizer, 0, wx.EXPAND | wx.ALL, 5)
        self.mainSizer.Add(self.log, 1, wx.EXPAND)

        self.SetSizer(self.mainSizer)
        self.refreshLog()

    def _handleEvent(self, event):
        if event.event in [labtronyx.EventCodes.script.changed]:
            self.update()

        elif event.event in [labtronyx.EventCodes.script.log]:
            if event.args[0] == self.controller.uuid:
                self.log.AppendText('\n' + event.args[1])

    def update(self):
        properties = self.controller.properties
        self.progress.SetValue(properties.get('progress'))

        self.status.SetLabelText(properties.get('status'))

    def refreshLog(self):
        log = self.controller.log
        log_txt = '\r\n'.join(log)
        self.log.SetEditable(True)
        self.log.SetLabelText(log_txt)
        self.log.SetEditable(False)


class ScriptResultsPanel(PanelViewBase):
    def __init__(self, parent, controller):
        assert(isinstance(controller, ScriptController))
        super(ScriptResultsPanel, self).__init__(parent, controller, id=wx.ID_ANY)

        self.list = ResultListCtrl(self, -1, style=wx.LC_REPORT)

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.list, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(self.mainSizer)

        self.update()

    def _handleEvent(self, event):
        if event.event in [labtronyx.EventCodes.script.changed]:
            results_displayed = self.list.GetItemCount()
            if len(self.controller.results) > results_displayed:
                self.update()

    def update(self):
        self.list.Freeze()

        self.list.ClearAll()
        self.list.InsertColumn(0, "Time")
        self.list.InsertColumn(1, "Result")
        self.list.InsertColumn(2, "Reason")
        self.list.InsertColumn(3, "Execution Time")

        properties = self.controller.properties
        results = reversed(self.controller.results)

        for res in results:
            res_time = self.controller.human_time(res.get('time', 0))
            idx = self.list.InsertStringItem(sys.maxint, res_time)
            self.list.SetStringItem(idx, 1, res.get('result', ''))
            self.list.SetStringItem(idx, 2, res.get('reason', ''))
            execTime = self.controller.human_time_delta(res.get('executionTime', 0))
            self.list.SetStringItem(idx, 3, execTime)

        self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE_USEHEADER)
        self.list.SetColumnWidth(2, 225)
        self.list.SetColumnWidth(3, 135)

        self.list.Thaw()


class ResultListCtrl(wx.ListCtrl):
    pass