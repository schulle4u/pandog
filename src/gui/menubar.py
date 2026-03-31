"""
Dynamic menu bar for PanDoG.

The menu structure changes depending on which notebook tab is active:
  Tab 0 (Converter): File, View, Help
  Tab 1 (Editor):    File, Edit, View, Help
"""

import wx

from utils.i18n import _

# Notebook tab indices
TAB_CONVERTER = 0
TAB_EDITOR = 1

# Custom menu IDs
ID_SETTINGS = wx.NewIdRef()
ID_CLEAR_RECENT = wx.NewIdRef()


class DynamicMenuBar:
    """
    Builds and manages two menu bar configurations and swaps them
    when the active tab changes.
    """

    def __init__(self, frame):
        self._frame = frame
        self._converter_menubar = self._build_converter_menubar()
        self._editor_menubar = self._build_editor_menubar()
        frame.SetMenuBar(self._converter_menubar)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_for_tab(self, tab_index: int):
        """Swap the menu bar to match the active tab."""
        if tab_index == TAB_EDITOR:
            self._frame.SetMenuBar(self._editor_menubar)
        else:
            self._frame.SetMenuBar(self._converter_menubar)

    def rebuild(self):
        """Rebuild both menu bars (e.g., after language change or recent-files update)."""
        self._converter_menubar = self._build_converter_menubar()
        self._editor_menubar = self._build_editor_menubar()
        if self._frame.notebook.GetSelection() == TAB_EDITOR:
            self._frame.SetMenuBar(self._editor_menubar)
        else:
            self._frame.SetMenuBar(self._converter_menubar)

    # ------------------------------------------------------------------
    # Menu bar builders
    # ------------------------------------------------------------------

    def _build_converter_menubar(self) -> wx.MenuBar:
        mb = wx.MenuBar()
        mb.Append(self._build_file_menu_converter(), _("&File"))
        mb.Append(self._build_view_menu(), _("&View"))
        mb.Append(self._build_help_menu(), _("&Help"))
        return mb

    def _build_editor_menubar(self) -> wx.MenuBar:
        mb = wx.MenuBar()
        mb.Append(self._build_file_menu_editor(), _("&File"))
        mb.Append(self._build_edit_menu(), _("&Edit"))
        mb.Append(self._build_view_menu(), _("&View"))
        mb.Append(self._build_help_menu(), _("&Help"))
        return mb

    # ------------------------------------------------------------------
    # Individual menus
    # ------------------------------------------------------------------

    def _build_file_menu_converter(self) -> wx.Menu:
        menu = wx.Menu()
        item_add = menu.Append(wx.ID_OPEN, _("&Add files...\tCtrl+O"))
        menu.AppendSeparator()
        self._append_recent_submenu(menu)
        menu.AppendSeparator()
        item_settings = menu.Append(ID_SETTINGS, _("&Settings...\tCtrl+,"))
        menu.AppendSeparator()
        item_quit = menu.Append(wx.ID_EXIT, _("&Quit\tAlt+F4"))

        self._frame.Bind(wx.EVT_MENU, self._frame.on_menu_add_files, item_add)
        self._frame.Bind(wx.EVT_MENU, self._frame.on_menu_settings, item_settings)
        self._frame.Bind(wx.EVT_MENU, self._frame.on_menu_quit, item_quit)
        return menu

    def _build_file_menu_editor(self) -> wx.Menu:
        menu = wx.Menu()
        item_new = menu.Append(wx.ID_NEW, _("&New\tCtrl+N"))
        item_open = menu.Append(wx.ID_OPEN, _("&Open...\tCtrl+O"))
        menu.AppendSeparator()
        item_save = menu.Append(wx.ID_SAVE, _("&Save\tCtrl+S"))
        item_save_as = menu.Append(wx.ID_SAVEAS, _("Save &As...\tCtrl+Shift+S"))
        menu.AppendSeparator()
        self._append_recent_submenu(menu)
        menu.AppendSeparator()
        item_settings = menu.Append(ID_SETTINGS, _("&Settings...\tCtrl+,"))
        menu.AppendSeparator()
        item_quit = menu.Append(wx.ID_EXIT, _("&Quit\tAlt+F4"))

        self._frame.Bind(wx.EVT_MENU, self._frame.on_menu_new, item_new)
        self._frame.Bind(wx.EVT_MENU, self._frame.on_menu_open_editor, item_open)
        self._frame.Bind(wx.EVT_MENU, self._frame.on_menu_save, item_save)
        self._frame.Bind(wx.EVT_MENU, self._frame.on_menu_save_as, item_save_as)
        self._frame.Bind(wx.EVT_MENU, self._frame.on_menu_settings, item_settings)
        self._frame.Bind(wx.EVT_MENU, self._frame.on_menu_quit, item_quit)
        return menu

    def _build_edit_menu(self) -> wx.Menu:
        menu = wx.Menu()
        item_undo = menu.Append(wx.ID_UNDO, _("&Undo\tCtrl+Z"))
        item_redo = menu.Append(wx.ID_REDO, _("&Redo\tCtrl+Y"))
        menu.AppendSeparator()
        item_cut = menu.Append(wx.ID_CUT, _("Cu&t\tCtrl+X"))
        item_copy = menu.Append(wx.ID_COPY, _("&Copy\tCtrl+C"))
        item_paste = menu.Append(wx.ID_PASTE, _("&Paste\tCtrl+V"))
        menu.AppendSeparator()
        item_select_all = menu.Append(wx.ID_SELECTALL, _("Select &all\tCtrl+A"))

        self._frame.Bind(wx.EVT_MENU, self._frame.on_menu_undo, item_undo)
        self._frame.Bind(wx.EVT_MENU, self._frame.on_menu_redo, item_redo)
        self._frame.Bind(wx.EVT_MENU, self._frame.on_menu_cut, item_cut)
        self._frame.Bind(wx.EVT_MENU, self._frame.on_menu_copy, item_copy)
        self._frame.Bind(wx.EVT_MENU, self._frame.on_menu_paste, item_paste)
        self._frame.Bind(wx.EVT_MENU, self._frame.on_menu_select_all, item_select_all)
        return menu

    def _build_view_menu(self) -> wx.Menu:
        menu = wx.Menu()
        item_converter = menu.Append(wx.ID_ANY, _("&Converter tab\tCtrl+1"))
        item_editor = menu.Append(wx.ID_ANY, _("&Editor tab\tCtrl+2"))

        self._frame.Bind(wx.EVT_MENU, lambda e: self._frame.notebook.SetSelection(TAB_CONVERTER), item_converter)
        self._frame.Bind(wx.EVT_MENU, lambda e: self._frame.notebook.SetSelection(TAB_EDITOR), item_editor)
        return menu

    def _build_help_menu(self) -> wx.Menu:
        menu = wx.Menu()
        item_about = menu.Append(wx.ID_ABOUT, _("&About PanDoG..."))
        self._frame.Bind(wx.EVT_MENU, self._frame.on_menu_about, item_about)
        return menu

    def _append_recent_submenu(self, parent_menu: wx.Menu):
        """Add a 'Recently opened' submenu populated from config."""
        recent_menu = wx.Menu()
        recent_files = self._frame.config.get_recent_files()

        if recent_files:
            for path in recent_files:
                item = recent_menu.Append(wx.ID_ANY, path)
                self._frame.Bind(wx.EVT_MENU, lambda e, p=path: self._frame.on_open_recent(p), item)
            recent_menu.AppendSeparator()

        item_clear = recent_menu.Append(ID_CLEAR_RECENT, _("Clear list"))
        self._frame.Bind(wx.EVT_MENU, self._frame.on_menu_clear_recent, item_clear)

        parent_menu.AppendSubMenu(recent_menu, _("Recently &opened"))
