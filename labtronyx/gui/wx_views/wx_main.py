__author__ = 'kkennedy'

# System Imports
import sys
import os
import logging
import traceback

import wx
import wx.aui
import wx.lib
import wx.lib.mixins.inspection
from wx.lib.agw import genericmessagedialog

# Labtronyx
import labtronyx

# Package Relative Imports
from ..controllers import MainApplicationController

# View Imports
from . import FrameViewBase, PanelViewBase, DialogViewBase
from . import ScriptBrowserPanel, ScriptInfoPanel
from . import InterfaceInfoPanel
from . import ResourceInfoPanel


def main(controller):
    app = LabtronyxApp(controller)
    app.MainLoop()


class LabtronyxApp(wx.App, wx.lib.mixins.inspection.InspectionMixin):
    def __init__(self, controller):
        self._controller = controller
        wx.App.__init__(self)

    def OnInit(self):
        self.Init()

        self.SetAppName("Labtronyx")

        main_view = MainView(self._controller)
        main_view.Show()
        self.SetTopWindow(main_view)

        # Unhandled exception handling
        sys.excepthook = self.OnException

        return True

    def OnException(self, etype, value, trace):
        msg = "".join(traceback.format_exception(etype, value, trace))
        msgbox = genericmessagedialog.GenericMessageDialog(None, msg, "Unhandled Exception",
                                                  wx.OK|wx.ICON_ERROR)
        msgbox.ShowModal()


class MainView(FrameViewBase):
    """
    Labtronyx Top-Level Window

    :type controller: MainApplicationController
    """

    def __init__(self, controller):
        assert(isinstance(controller, MainApplicationController))
        super(MainView, self).__init__(None, controller,
                                       id=-1, title="Labtronyx", size=(640, 480), style=wx.DEFAULT_FRAME_STYLE)

        self.mainPanel = wx.Panel(self)
        self.aui_mgr = wx.aui.AuiManager()
        self.aui_mgr.SetManagedWindow(self.mainPanel)

        # Build Menu
        self.buildMenubar()

        # Build Left Panel
        self.pnl_left = wx.Panel(self.mainPanel, style=wx.TAB_TRAVERSAL | wx.CLIP_CHILDREN)
        # Resource Tree
        self.tree = wx.TreeCtrl(self.pnl_left, -1, style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT)
        self.host = wx.Choice(self.pnl_left, -1, style=wx.CB_SORT)
        self.updateHostSelector()
        self.host.SetSelection(0)
        host_select_sizer = wx.BoxSizer(wx.HORIZONTAL)
        host_select_sizer.Add(self.host, 1, wx.EXPAND)

        leftPanelSizer = wx.BoxSizer(wx.VERTICAL)
        leftPanelSizer.Add(wx.StaticText(self.pnl_left, -1, "Select Host"), 0, wx.ALL, 5)
        leftPanelSizer.Add(host_select_sizer, 0, wx.EXPAND | wx.BOTTOM, 5)
        leftPanelSizer.Add(self.tree, 1, wx.EXPAND)
        self.pnl_left.SetSizer(leftPanelSizer)
        # self.pnl_left.Fit()
        self.buildTree()

        # Build Main Panel
        self.pnl_content = wx.Panel(self.mainPanel, size=wx.DefaultSize,
                                    style=wx.TAB_TRAVERSAL | wx.CLIP_CHILDREN | wx.FULL_REPAINT_ON_RESIZE)

        # Build Log
        self.log = wx.TextCtrl(self.mainPanel, -1, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        self.buildLog()

        # Event bindings
        self.Bind(wx.EVT_CHOICE, self.e_OnHostSelect, self.host)
        self.Bind(wx.EVT_CLOSE, self.e_OnWindowClose)

        self.SetBackgroundColour(wx.NullColour)
        self.SetSize((800, 600))

        self.aui_mgr.AddPane(self.pnl_content, wx.aui.AuiPaneInfo().CenterPane().Name("Content"))
        self.aui_mgr.AddPane(self.log, wx.aui.AuiPaneInfo().Bottom().BestSize((-1, 200)).Caption("Log Messages").
                             Floatable(False).CloseButton(False).Name("LogPanel"))
        self.aui_mgr.AddPane(self.pnl_left, wx.aui.AuiPaneInfo().Left().BestSize((300, -1)).
                             Floatable(False).CloseButton(False).MinSize((240, -1)).Resizable(True).
                             Caption("Resources").Name("ResourceTree"))
        self.aui_mgr.Update()

        self.Fit()

    def buildMenubar(self):
        self.menubar = wx.MenuBar()

        # File
        self.menu_file = wx.Menu()
        item = self.menu_file.Append(-1, "E&xit\tCtrl-Q", "Exit")
        self.Bind(wx.EVT_MENU, self.e_MenuExit, item)

        self.menubar.Append(self.menu_file, "&File")

        # Set frame menubar
        self.SetMenuBar(self.menubar)

    def buildTree(self):
        # Build image list
        isz = (16, 16)
        self.il = wx.ImageList(*isz)
        self.art_resource = self.il.Add(wx.Image(
            os.path.join(self.controller.rootPath, "images", "hard-drive-2x.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.art_interface = self.il.Add(wx.Image(
            os.path.join(self.controller.rootPath, "images", "fork-2x.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.art_script = self.il.Add(wx.Image(
            os.path.join(self.controller.rootPath, "images", "file-2x.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap())

        self.tree.SetImageList(self.il)

        self.pnode_root = self.tree.AddRoot("Labtronyx")  # Add hidden root item
        self.tree.SetPyData(self.pnode_root, None)

        self.updateTree()
        # self.tree.GetMainWindow().Bind(wx.EVT_RIGHT_UP, self.e_OnRightClick)
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.e_OnTreeSelect)

    def buildLog(self):
        # Create handler for logger
        self.logger.addHandler(WxLogHandler(self.log))
        self.logger.setLevel(logging.DEBUG)

        self.logger.info("Logger attached")

    def updateHostSelector(self):
        selected = self.host.GetStringSelection()

        choices = [hcon.hostname for hcon in self.controller.hosts.values()]

        self.host.Clear()
        self.host.AppendItems(choices)

        if selected in choices:
            self.host.SetStringSelection(selected)

    def get_selected_host_controller(self):
        hostname = self.host.GetStringSelection()
        return self.controller.get_host(hostname)

    def updateTree(self):
        host_controller = self.get_selected_host_controller()

        if host_controller is None:
            return

        self.tree.DeleteChildren(self.pnode_root)
        # Resources
        self.pnode_resources = self.tree.AppendItem(self.pnode_root, 'Resources')
        self.tree.SetItemImage(self.pnode_resources, self.art_resource)
        self.nodes_resources = {}
        # Interfaces
        self.pnode_interfaces = self.tree.AppendItem(self.pnode_root, 'Interfaces')
        self.tree.SetItemImage(self.pnode_interfaces, self.art_interface)
        self.nodes_interfaces = {}
        # Scripts
        self.pnode_scripts = self.tree.AppendItem(self.pnode_root, 'Scripts')
        self.tree.SetItemImage(self.pnode_scripts, self.art_script)
        self.nodes_scripts = {}

        for uuid, prop in host_controller.properties.items():
            if prop.get('pluginType') == 'resource':
                node_name = prop.get('resourceID')
                child = self.tree.AppendItem(self.pnode_resources, node_name)
                self.tree.SetPyData(child, uuid)
                self.tree.SetItemImage(child, self.art_resource)
                self.nodes_resources[uuid] = child

            elif prop.get('pluginType') == 'interface':
                node_name = prop.get('interfaceName')
                child = self.tree.AppendItem(self.pnode_interfaces, node_name)
                self.tree.SetPyData(child, uuid)
                self.tree.SetItemImage(child, self.art_interface)
                self.nodes_interfaces[uuid] = child

            elif prop.get('pluginType') == 'script':
                node_name = prop.get('fqn')
                child = self.tree.AppendItem(self.pnode_scripts, node_name)
                self.tree.SetPyData(child, uuid)
                self.tree.SetItemImage(child, self.art_script)
                self.nodes_scripts[uuid] = child

        self.tree.SortChildren(self.pnode_resources)
        self.tree.Expand(self.pnode_resources)

    def e_MenuExit(self, event):
        self.Close(True)

    def e_OnWindowClose(self, event):
        self.Destroy()

    def e_OnTreeSelect(self, event):
        item = event.GetItem()
        item_data = self.tree.GetPyData(item)

        host_controller = self.get_selected_host_controller()

        if host_controller is not None:
            if item == self.pnode_resources:
                self.clearContentPanel()

            elif item == self.pnode_interfaces:
                self.clearContentPanel()

            elif item == self.pnode_scripts:
                self.loadScriptSummary()

            elif item_data in host_controller.properties:
                item_props = host_controller.properties.get(item_data)

                if item_props.get('pluginType') == 'resource':
                    self.loadResourcePanel(item_data)

                elif item_props.get('pluginType') == 'interface':
                    self.loadInterfacePanel(item_data)

                elif item_props.get('pluginType') == 'script':
                    self.loadScriptPanel(item_data)

                else:
                    self.clearContentPanel()

    def e_OnHostSelect(self, event):
        self.updateTree()

    def clearContentPanel(self):
        self.pnl_content.DestroyChildren()

    def _loadContentPanel(self, panel, title):
        self.pnl_content.Freeze()

        # Title
        lbl = wx.StaticText(self.pnl_content, -1, title)
        lbl.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))

        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer.Add(lbl, 0, wx.EXPAND | wx.ALL, 5)
        panelSizer.Add(wx.StaticLine(self.pnl_content), 0, wx.EXPAND | wx.ALL, 5)
        panelSizer.Add(panel, 1, wx.EXPAND | wx.ALL, 5)
        self.pnl_content.SetSizer(panelSizer)
        self.pnl_content.Layout()

        # Force new panel to use all available space
        # panel.SetSize(self.pnl_content.GetSize())

        self.pnl_content.Thaw()

    def loadInterfacePanel(self, int_uuid):
        host_controller = self.get_selected_host_controller()
        int_controller = host_controller.get_interface(int_uuid)

        # Build panel
        self.clearContentPanel()
        int_panel = InterfaceInfoPanel(self.pnl_content, int_controller)
        self._loadContentPanel(int_panel, "Interface Details")

    def loadResourcePanel(self, res_uuid):
        host_controller = self.get_selected_host_controller()
        res_controller = host_controller.get_resource(res_uuid)

        # Build panel
        self.clearContentPanel()
        res_panel = ResourceInfoPanel(self.pnl_content, res_controller)
        self._loadContentPanel(res_panel, "Resource Details")

    def loadScriptPanel(self, script_uuid):
        host_controller = self.get_selected_host_controller()
        scr_controller = host_controller.get_script(script_uuid)

        self.clearContentPanel()
        scr_panel = ScriptInfoPanel(self.pnl_content, scr_controller)
        self._loadContentPanel(scr_panel, "Script Details")

    def loadScriptSummary(self):
        host_controller = self.get_selected_host_controller()

        # Build panel
        self.clearContentPanel()
        new_panel = ScriptBrowserPanel(self.pnl_content, host_controller)
        self._loadContentPanel(new_panel, "Scripts")

    def _handleEvent(self, event):
        self.logger.debug("[EVENT] - %s - %s", event.hostname, event.event)

        if event.event in [labtronyx.EventCodes.manager.heartbeat]:
            pass

        elif event.event in [labtronyx.EventCodes.resource.created,
                             labtronyx.EventCodes.resource.destroyed]:
            self.updateTree()

        elif event.event in [labtronyx.EventCodes.script.created,
                             labtronyx.EventCodes.script.destroyed]:
            self.updateTree()

        elif event.event in [labtronyx.EventCodes.interface.created,
                             labtronyx.EventCodes.interface.destroyed]:
            self.updateTree()

        elif event.event in [labtronyx.EventCodes.resource.changed,
                             labtronyx.EventCodes.resource.driver_loaded,
                             labtronyx.EventCodes.resource.driver_unloaded]:
            pass


class WxLogHandler(logging.Handler):
    def __init__(self, text_control):
        logging.Handler.__init__(self)

        assert (isinstance(text_control, wx.TextCtrl))
        self.control = text_control

    def emit(self, record):
        wx.CallAfter(self.wx_emit, record)

    def wx_emit(self, record):
        self.control.AppendText('\n' + self.format(record))