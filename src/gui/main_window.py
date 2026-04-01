"""
Main application window for PanDoG
"""

import wx
import wx.adv

from config.config_manager import ConfigManager
from config.defaults import APP_NAME, APP_VERSION, APP_AUTHOR, APP_WEBSITE, APP_LICENSE
from core.converter import PandocConverter
from gui.notebook import MainNotebook
from gui.menubar import DynamicMenuBar
from gui.statusbar import AppStatusBar
from gui.dialogs.settings import SettingsDialog
from gui.theme_manager import ThemeManager
from utils.i18n import _, initialize_i18n
from utils.logger import get_logger, configure_logging

logger = get_logger('main_window')


class MainFrame(wx.Frame):
    """
    Top-level application window.

    Owns the config, converter, notebook, menu bar, and status bar.
    Handles menu events and delegates to the appropriate panel.
    """

    def __init__(self, config: ConfigManager, theme_manager: ThemeManager):
        self.config = config
        self.theme_manager = theme_manager

        width = config.getint('UI', 'window_width', fallback=1200)
        height = config.getint('UI', 'window_height', fallback=800)

        super().__init__(
            parent=None,
            title=APP_NAME,
            size=(width, height),
        )
        self.SetName('main_window')

        # Restore window position if saved
        x = config.get('UI', 'window_x', fallback='')
        y = config.get('UI', 'window_y', fallback='')
        if x and y:
            try:
                self.SetPosition((int(x), int(y)))
            except ValueError:
                self.Centre()
        else:
            self.Centre()

        # Core objects
        pandoc_path = config.get('Converter', 'pandoc_path', fallback='pandoc')
        self._converter = PandocConverter(pandoc_path)
        if not self._converter.is_available():
            wx.MessageBox(
                _("Pandoc is not available at: '{}' Please check that Pandoc has been installed correctly.").format(pandoc_path),
                _("Error"),
                wx.OK | wx.ICON_ERROR
            )

        # Build UI
        self.statusbar = AppStatusBar(self)
        self.SetStatusBar(self.statusbar)

        self.notebook = MainNotebook(self, self._converter, self.statusbar,
                                     on_files_added=self._on_converter_files_added)

        self._menubar = DynamicMenuBar(self)

        # Notebook page change → swap menu bar
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._on_tab_changed)
        self.Bind(wx.EVT_CLOSE, self._on_close)

        # Apply theme and register callback for live updates
        theme_manager.register_callback(lambda _t: theme_manager.apply_theme(self))
        theme_manager.apply_theme(self)

        # Sync status bar to initial tab (Converter)
        self.statusbar.clear_editor_info()

        logger.info("Main window initialised.")

    # ------------------------------------------------------------------
    # Tab switching
    # ------------------------------------------------------------------

    def _on_tab_changed(self, event):
        tab = event.GetSelection()
        self._menubar.update_for_tab(tab)
        if tab == 1:
            # Switching to editor: show editor info, hide converter status
            self.statusbar.clear_converter_status()
            self.notebook.editor_panel._update_statusbar_info()
        else:
            self.statusbar.clear_editor_info()
        event.Skip()

    # ------------------------------------------------------------------
    # Window close
    # ------------------------------------------------------------------

    def _on_close(self, event):
        # Check for unsaved editor changes
        if not self.notebook.editor_panel.check_unsaved():
            event.Veto()
            return

        # Save window geometry
        size = self.GetSize()
        pos = self.GetPosition()
        self.config.set('UI', 'window_width', size.width)
        self.config.set('UI', 'window_height', size.height)
        self.config.set('UI', 'window_x', pos.x)
        self.config.set('UI', 'window_y', pos.y)
        self.config.save()
        logger.info("Application closing.")
        event.Skip()

    # ------------------------------------------------------------------
    # Menu event handlers
    # ------------------------------------------------------------------

    def _on_converter_files_added(self, paths: list):
        """Called by ConverterPanel whenever files are added via its own buttons."""
        for p in paths:
            self.config.add_recent_file(p)
        self._menubar.rebuild()

    def on_menu_add_files(self, _event):
        with wx.FileDialog(
            self,
            message=_("Add files"),
            style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                paths = dlg.GetPaths()
                self.notebook.converter_panel.add_files(paths)

    def on_menu_new(self, _event):
        self.notebook.editor_panel.new_document()

    def on_menu_open_editor(self, _event):
        with wx.FileDialog(
            self,
            message=_("Open file"),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                self.notebook.editor_panel.open_file(path)
                self.config.add_recent_file(path)
                self._menubar.rebuild()

    def on_menu_save(self, _event):
        self.notebook.editor_panel.save_file()

    def on_menu_save_as(self, _event):
        self.notebook.editor_panel.show_save_as_dialog()

    def on_menu_settings(self, _event):
        with SettingsDialog(self, self.config, self.theme_manager) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self._apply_settings()

    def on_menu_quit(self, _event):
        self.Close()

    def on_open_recent(self, path: str):
        """Open a recently used file in the appropriate panel."""
        tab = self.notebook.GetSelection()
        if tab == 1:
            self.notebook.editor_panel.open_file(path)
            self.config.add_recent_file(path)
            self._menubar.rebuild()
        else:
            # Callback in ConverterPanel handles add_recent_file + rebuild
            self.notebook.converter_panel.add_files([path])

    def on_menu_clear_recent(self, _event):
        self.config.clear_recent_files()
        self._menubar.rebuild()

    # Edit menu (editor tab)
    def on_menu_undo(self, _event):
        tc = self.notebook.editor_panel._text_ctrl
        if tc.CanUndo():
            tc.Undo()

    def on_menu_redo(self, _event):
        tc = self.notebook.editor_panel._text_ctrl
        if tc.CanRedo():
            tc.Redo()

    def on_menu_cut(self, _event):
        self.notebook.editor_panel._text_ctrl.Cut()

    def on_menu_copy(self, _event):
        self.notebook.editor_panel._text_ctrl.Copy()

    def on_menu_paste(self, _event):
        self.notebook.editor_panel._text_ctrl.Paste()

    def on_menu_select_all(self, _event):
        self.notebook.editor_panel._text_ctrl.SelectAll()

    def on_menu_about(self, _event):
        info = wx.adv.AboutDialogInfo()
        info.SetName(APP_NAME)
        info.SetVersion(APP_VERSION)
        info.SetDescription(_("An accessible cross-platform GUI for Pandoc."))
        info.SetCopyright(f"\u00a9 {APP_AUTHOR}")
        info.SetWebSite(APP_WEBSITE)
        info.SetLicence(APP_LICENSE)
        wx.adv.AboutBox(info)

    # ------------------------------------------------------------------
    # Settings application
    # ------------------------------------------------------------------

    def _apply_settings(self):
        """Apply changed settings without restarting."""
        # Update pandoc path
        new_path = self.config.get('Converter', 'pandoc_path', fallback='pandoc')
        if self._converter.pandoc_path != new_path:
            self._converter.pandoc_path = new_path
            self._converter.invalidate_format_cache()
            self.notebook.converter_panel.reload_formats()
            self.notebook.editor_panel.reload_formats(self._converter.get_output_formats())

        # Update logging
        configure_logging(
            level=self.config.get('Logging', 'level', fallback='INFO'),
            file_logging=self.config.getboolean('Logging', 'file_logging', fallback=True),
            console_logging=self.config.getboolean('Logging', 'console_logging', fallback=False),
        )

        # Rebuild menu (e.g. language change)
        self._menubar.rebuild()

        self.statusbar.set_status(_("Settings saved."))
