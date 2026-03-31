"""
Main notebook with Converter and Editor tabs
"""

import wx

from core.converter import PandocConverter
from gui.converter.panel import ConverterPanel
from gui.editor.panel import EditorPanel
from gui.statusbar import AppStatusBar
from utils.i18n import _

TAB_CONVERTER = 0
TAB_EDITOR = 1


class MainNotebook(wx.Notebook):
    """
    Two-tab notebook: Converter and Editor.
    Ctrl+Tab cycles through tabs via an accelerator table.
    """

    def __init__(self, parent, converter: PandocConverter, statusbar: AppStatusBar, on_files_added=None):
        super().__init__(parent, style=wx.NB_TOP)
        self.SetName('main_notebook')

        self.converter_panel = ConverterPanel(self, converter, statusbar, on_files_added=on_files_added)
        self.editor_panel = EditorPanel(self, converter, statusbar)

        self.AddPage(self.converter_panel, _("Converter"))
        self.AddPage(self.editor_panel, _("Editor"))

        # Populate editor output formats after converter has loaded them
        self.editor_panel.load_output_formats(converter.get_output_formats())

        self._setup_accelerators(parent)

    def _setup_accelerators(self, frame):
        """Bind Ctrl+Tab / Ctrl+Shift+Tab to cycle notebook tabs."""
        id_next = wx.NewIdRef()
        id_prev = wx.NewIdRef()
        frame.Bind(wx.EVT_MENU, self._on_next_tab, id=id_next)
        frame.Bind(wx.EVT_MENU, self._on_prev_tab, id=id_prev)
        accel_entries = [
            wx.AcceleratorEntry(wx.ACCEL_CTRL, wx.WXK_TAB, id_next),
            wx.AcceleratorEntry(wx.ACCEL_CTRL | wx.ACCEL_SHIFT, wx.WXK_TAB, id_prev),
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('1'), wx.NewIdRef()),
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('2'), wx.NewIdRef()),
        ]
        frame.SetAcceleratorTable(wx.AcceleratorTable(accel_entries))

    def _on_next_tab(self, _event):
        n = self.GetPageCount()
        self.SetSelection((self.GetSelection() + 1) % n)

    def _on_prev_tab(self, _event):
        n = self.GetPageCount()
        self.SetSelection((self.GetSelection() - 1) % n)
