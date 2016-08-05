import wx

import labtronyx

from ..controllers import ManagerController
from . import FrameViewBase, PanelViewBase, DialogViewBase


class ScriptBrowserPanel(PanelViewBase):
    def __init__(self, parent, controller):
        assert(isinstance(controller, ManagerController))
        super(ScriptBrowserPanel, self).__init__(parent, controller, id=wx.ID_ANY)

        self.tree = wx.TreeCtrl(self, -1, style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT)
        self.pnode_root = self.tree.AddRoot("Scripts")  # Add hidden root item
        self.tree.SetPyData(self.pnode_root, None)

        self.panel_detail = wx.Panel(self)
        self.panel_detail.SetMinSize((250, -1))

        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.e_OnTreeSelect)

        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mainSizer.Add(self.tree, 1, wx.EXPAND)
        self.mainSizer.Add(wx.StaticLine(self, style=wx.LI_VERTICAL), 0, wx.EXPAND | wx.ALL, 5)
        self.mainSizer.Add(self.panel_detail, 0, wx.EXPAND)
        self.SetSizer(self.mainSizer)

        self.updateTree()

    def updateTree(self):
        self.tree.DeleteChildren(self.pnode_root)
        attributes = self.controller.get_script_attributes()

        categories = set([attr.get('category') for fqn, attr in attributes.items()])
        self.nodes_categories = {}

        for cat in categories:
            child = self.tree.AppendItem(self.pnode_root, cat)
            self.nodes_categories[cat] = child

        for fqn, attr in attributes.items():
            cat_node = self.nodes_categories.get(attr.get('category'))

            child = self.tree.AppendItem(cat_node, fqn)
            self.tree.SetPyData(child, fqn)

        #     subcategories = set([attr.get('subcategory') for fqn, attr in attributes.items()
        #                          if attr.get('category') == categories])

    def clearScriptSummary(self):
        self.panel_detail.DestroyChildren()

    def loadScriptSummary(self, fqn):
        self.panel_detail.Freeze()
        self.clearScriptSummary()

        new_panel = ScriptSummaryPanel(self.panel_detail, self.controller, fqn)

        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        panel_sizer.Add(new_panel, 1, wx.EXPAND)
        self.panel_detail.SetSizer(panel_sizer)
        self.panel_detail.Layout()

        self.panel_detail.Thaw()

    def e_OnTreeSelect(self, event):
        item = event.GetItem()
        item_data = self.tree.GetPyData(item)

        if item_data is not None:
            self.loadScriptSummary(item_data)

        else:
            self.clearScriptSummary()


class ScriptSummaryPanel(PanelViewBase):
    def __init__(self, parent, controller, fqn):
        assert (isinstance(controller, ManagerController))
        super(ScriptSummaryPanel, self).__init__(parent, controller, id=wx.ID_ANY)

        self.fqn = fqn
        self.attributes = self.controller.attributes.get(fqn, {})
        self.params = self.attributes.get('parameters')

        # Attributes
        self.attrSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        self._createField("Script Name", "name")
        self._createField("Description", "description")
        self._createField("Author", "author")
        self._createField("Version", "version")
        self._createField("Category", "category")

        if self.attributes.get("subcategory") != '':
            self._createField("Subcategory", "subcategory")
        self.attrSizer.AddGrowableCol(1)

        self.btn_create = wx.Button(self, -1, "Create Instance")
        self.Bind(wx.EVT_BUTTON, self.e_OnClick, self.btn_create)

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.attrSizer, 1, wx.EXPAND)
        self.mainSizer.Add(self.btn_create, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        self.SetSizer(self.mainSizer)
        self.SetAutoLayout(True)

    def _createField(self, label, prop_key):
        self._gridText_attr(label, self.attributes.get(prop_key))

    def _gridText_attr(self, label, text):
        if label != '':
            label += ":"

        lblNew = wx.StaticText(self, -1, label)
        txtNew = wx.StaticText(self, -1, text)
        txtNew.Wrap(170)

        self.attrSizer.Add(lblNew, 0, wx.ALIGN_RIGHT | wx.RIGHT, 5)
        self.attrSizer.Add(txtNew, 1, wx.ALIGN_LEFT | wx.EXPAND)

    def e_OnClick(self, event):
        if len(self.params) > 0:
            param_dialog = ScriptParametersDialog(self, self.controller, self.fqn)
            ret_code = param_dialog.ShowModal()

            if ret_code != wx.ID_OK:
                return

            params = param_dialog.getParams()

        else:
            params = {}

        self.controller.create_script_instance(self.fqn, **params)


class ScriptParametersDialog(DialogViewBase):
    def __init__(self, parent, controller, fqn):
        assert (isinstance(controller, ManagerController))
        super(ScriptParametersDialog, self).__init__(parent, controller, id=wx.ID_ANY, title="Script Parameters")

        self.attributes = self.controller.attributes.get(fqn, {})
        self.params = self.attributes.get('parameters')
        self._fields = {}

        lbl = wx.StaticText(self, -1, "Open Script")
        lbl.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))

        btnOk = wx.Button(self, wx.ID_OK, "&Ok")
        btnOk.SetDefault()
        btnCancel = wx.Button(self, wx.ID_CANCEL, "&Cancel")

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(btnOk)
        btnSizer.AddButton(btnCancel)
        btnSizer.Realize()

        self.paramSizer = wx.BoxSizer(wx.VERTICAL)
        for param_attr, param_info in self.params.items():
            self._createField(param_attr)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(lbl, 0, wx.EXPAND | wx.ALL, border=5)
        mainSizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.ALL, border=5)
        mainSizer.Add(self.paramSizer, 0, wx.EXPAND | wx.ALL, border=5)
        mainSizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.ALL, border=5)
        mainSizer.Add(btnSizer, 0, wx.ALL | wx.ALIGN_RIGHT, border=5)

        self.SetSizer(mainSizer)
        mainSizer.Fit(self)

    def _createField(self, param_attr):
        param_info = self.params.get(param_attr)

        fieldSizer = wx.BoxSizer(wx.HORIZONTAL)
        lbl_attr = wx.StaticText(self, -1, param_attr, size=(150, -1))
        lbl_desc = wx.StaticText(self, -1, param_info.get('description'), size=(150, -1))
        lbl_desc.SetFont(wx.Font(8, wx.DEFAULT, wx.ITALIC, wx.NORMAL))
        lbl_desc.Wrap(150)
        txt_val = wx.TextCtrl(self, -1, size=(150, -1))
        self._fields[param_attr] = txt_val

        descSizer = wx.BoxSizer(wx.VERTICAL)
        descSizer.Add(lbl_attr, 0)
        descSizer.Add(lbl_desc, 0)
        fieldSizer.Add(descSizer, 0, wx.ALIGN_LEFT | wx.EXPAND)
        fieldSizer.Add(txt_val, 1, wx.ALIGN_RIGHT)
        self.paramSizer.Add(fieldSizer, 0, wx.EXPAND | wx.ALL, 5)

    def getParams(self):
        params = {}

        for fieldname, field_ctrl in self._fields.items():
            params[fieldname] = field_ctrl.GetValue()

        return params