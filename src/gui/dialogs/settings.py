"""
Settings dialog for PanDoG
"""

import wx

from config.config_manager import ConfigManager
from gui.theme_manager import ThemeManager
from utils.i18n import _, get_i18n, LANGUAGE_NAMES
from utils.logger import get_logger, configure_logging

logger = get_logger('settings')

_THEMES = ['system', 'light', 'dark']
_LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


class SettingsDialog(wx.Dialog):
    """
    Modal settings dialog with three tabs:
      - General (language, theme)
      - Converter (pandoc path, output directory, default formats)
      - Logging (log level, file/console logging)
    """

    def __init__(self, parent, config: ConfigManager, theme_manager: ThemeManager):
        super().__init__(
            parent,
            title=_("Settings"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.SetName('settings_dialog')
        self._config = config
        self._theme_manager = theme_manager
        self._build_ui()
        self._load_values()
        self.Fit()
        self.SetMinSize((480, 360))

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        self._notebook = wx.Notebook(self)
        self._notebook.SetName('settings_notebook')

        self._page_general = self._build_general_page()
        self._page_converter = self._build_converter_page()
        self._page_logging = self._build_logging_page()

        self._notebook.AddPage(self._page_general, _("General"))
        self._notebook.AddPage(self._page_converter, _("Converter"))
        self._notebook.AddPage(self._page_logging, _("Logging"))

        sizer.Add(self._notebook, 1, wx.EXPAND | wx.ALL, 6)
        sizer.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.EXPAND | wx.ALL, 6)

        self.SetSizer(sizer)
        self.Bind(wx.EVT_BUTTON, self._on_ok, id=wx.ID_OK)

    def _build_general_page(self) -> wx.Panel:
        page = wx.Panel(self._notebook)
        page.SetName('settings_general_page')
        sizer = wx.BoxSizer(wx.VERTICAL)

        box = wx.StaticBox(page, label=_("General settings"))
        box_sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        panel = wx.Panel(box)
        panel.SetName('general_inner_panel')
        grid = wx.FlexGridSizer(rows=0, cols=2, vgap=8, hgap=8)
        grid.AddGrowableCol(1)

        # Language
        lbl_lang = wx.StaticText(panel, label=_("Language:"))
        lbl_lang.SetName('lbl_language')
        self._choice_lang = wx.Choice(panel)
        self._choice_lang.SetName('choice_language')
        self._lang_codes = []
        for code, name in LANGUAGE_NAMES.items():
            self._choice_lang.Append(name)
            self._lang_codes.append(code)
        grid.Add(lbl_lang, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self._choice_lang, 1, wx.EXPAND)

        # Theme
        lbl_theme = wx.StaticText(panel, label=_("Theme:"))
        lbl_theme.SetName('lbl_theme')
        self._choice_theme = wx.Choice(panel)
        self._choice_theme.SetName('choice_theme')
        for t in _THEMES:
            self._choice_theme.Append(t)
        grid.Add(lbl_theme, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self._choice_theme, 1, wx.EXPAND)

        panel.SetSizer(grid)
        box_sizer.Add(panel, 0, wx.EXPAND | wx.ALL, 6)
        sizer.Add(box_sizer, 0, wx.EXPAND | wx.ALL, 6)
        page.SetSizer(sizer)
        return page

    def _build_converter_page(self) -> wx.Panel:
        page = wx.Panel(self._notebook)
        page.SetName('settings_converter_page')
        sizer = wx.BoxSizer(wx.VERTICAL)

        box = wx.StaticBox(page, label=_("Converter settings"))
        box_sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        panel = wx.Panel(box)
        panel.SetName('converter_inner_panel')
        grid = wx.FlexGridSizer(rows=0, cols=2, vgap=8, hgap=8)
        grid.AddGrowableCol(1)

        # Pandoc path
        lbl_pandoc = wx.StaticText(panel, label=_("Pandoc path:"))
        lbl_pandoc.SetName('lbl_pandoc_path')
        pandoc_row = wx.BoxSizer(wx.HORIZONTAL)
        self._txt_pandoc_path = wx.TextCtrl(panel)
        self._txt_pandoc_path.SetName('txt_pandoc_path')
        self._btn_browse_pandoc = wx.Button(panel, label=_("&Browse") + "...")
        self._btn_browse_pandoc.SetName('btn_browse_pandoc')
        pandoc_row.Add(self._txt_pandoc_path, 1, wx.EXPAND | wx.RIGHT, 4)
        pandoc_row.Add(self._btn_browse_pandoc)
        grid.Add(lbl_pandoc, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(pandoc_row, 1, wx.EXPAND)

        # Output directory
        lbl_out_dir = wx.StaticText(panel, label=_("Default output directory:"))
        lbl_out_dir.SetName('lbl_default_output_dir')
        outdir_row = wx.BoxSizer(wx.HORIZONTAL)
        self._txt_output_dir = wx.TextCtrl(panel)
        self._txt_output_dir.SetName('txt_default_output_dir')
        self._btn_browse_outdir = wx.Button(panel, label=_("B&rowse") + "...")
        self._btn_browse_outdir.SetName('btn_browse_output_dir')
        outdir_row.Add(self._txt_output_dir, 1, wx.EXPAND | wx.RIGHT, 4)
        outdir_row.Add(self._btn_browse_outdir)
        grid.Add(lbl_out_dir, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(outdir_row, 1, wx.EXPAND)

        # Same-dir default
        grid.Add((0, 0))
        self._chk_same_dir = wx.CheckBox(panel, label=_("Default: use same directory as input file"))
        self._chk_same_dir.SetName('chk_default_same_dir')
        grid.Add(self._chk_same_dir)

        panel.SetSizer(grid)
        box_sizer.Add(panel, 0, wx.EXPAND | wx.ALL, 6)
        sizer.Add(box_sizer, 0, wx.EXPAND | wx.ALL, 6)
        page.SetSizer(sizer)

        self._btn_browse_pandoc.Bind(wx.EVT_BUTTON, self._on_browse_pandoc)
        self._btn_browse_outdir.Bind(wx.EVT_BUTTON, self._on_browse_outdir)

        return page

    def _build_logging_page(self) -> wx.Panel:
        page = wx.Panel(self._notebook)
        page.SetName('settings_logging_page')
        sizer = wx.BoxSizer(wx.VERTICAL)

        box = wx.StaticBox(page, label=_("Logging settings"))
        box_sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        panel = wx.Panel(box)
        panel.SetName('logging_inner_panel')
        grid = wx.FlexGridSizer(rows=0, cols=2, vgap=8, hgap=8)
        grid.AddGrowableCol(1)

        # Log level
        lbl_level = wx.StaticText(panel, label=_("Log level:"))
        lbl_level.SetName('lbl_log_level')
        self._choice_log_level = wx.Choice(panel)
        self._choice_log_level.SetName('choice_log_level')
        for level in _LOG_LEVELS:
            self._choice_log_level.Append(level)
        grid.Add(lbl_level, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self._choice_log_level, 1, wx.EXPAND)

        # Checkboxes (span both columns)
        grid.Add((0, 0))
        self._chk_file_log = wx.CheckBox(panel, label=_("Write log to file"))
        self._chk_file_log.SetName('chk_file_logging')
        grid.Add(self._chk_file_log)

        grid.Add((0, 0))
        self._chk_console_log = wx.CheckBox(panel, label=_("Show log in console"))
        self._chk_console_log.SetName('chk_console_logging')
        grid.Add(self._chk_console_log)

        panel.SetSizer(grid)
        box_sizer.Add(panel, 0, wx.EXPAND | wx.ALL, 6)
        sizer.Add(box_sizer, 0, wx.EXPAND | wx.ALL, 6)
        page.SetSizer(sizer)
        return page

    # ------------------------------------------------------------------
    # Load / save values
    # ------------------------------------------------------------------

    def _load_values(self):
        # General
        lang = self._config.get('General', 'language', fallback='en')
        if lang in self._lang_codes:
            self._choice_lang.SetSelection(self._lang_codes.index(lang))
        else:
            self._choice_lang.SetSelection(0)

        theme = self._config.get('General', 'theme', fallback='system')
        if theme in _THEMES:
            self._choice_theme.SetSelection(_THEMES.index(theme))
        else:
            self._choice_theme.SetSelection(0)

        # Converter
        self._txt_pandoc_path.SetValue(self._config.get('Converter', 'pandoc_path', fallback='pandoc'))
        self._txt_output_dir.SetValue(self._config.get('Converter', 'output_dir', fallback=''))
        self._chk_same_dir.SetValue(self._config.getboolean('Converter', 'output_same_dir', fallback=True))

        # Logging
        level = self._config.get('Logging', 'level', fallback='INFO')
        if level in _LOG_LEVELS:
            self._choice_log_level.SetSelection(_LOG_LEVELS.index(level))
        else:
            self._choice_log_level.SetSelection(_LOG_LEVELS.index('INFO'))

        self._chk_file_log.SetValue(self._config.getboolean('Logging', 'file_logging', fallback=True))
        self._chk_console_log.SetValue(self._config.getboolean('Logging', 'console_logging', fallback=False))

    def _save_values(self):
        # General
        lang_sel = self._choice_lang.GetSelection()
        lang = self._lang_codes[lang_sel] if lang_sel != wx.NOT_FOUND else 'en'
        self._config.set('General', 'language', lang)

        theme_sel = self._choice_theme.GetSelection()
        theme = _THEMES[theme_sel] if theme_sel != wx.NOT_FOUND else 'system'
        self._config.set('General', 'theme', theme)
        # Apply immediately via ThemeManager (save=False, config.save() below handles persistence)
        self._theme_manager.set_theme(theme, save=False)

        # Converter
        self._config.set('Converter', 'pandoc_path', self._txt_pandoc_path.GetValue().strip())
        self._config.set('Converter', 'output_dir', self._txt_output_dir.GetValue().strip())
        self._config.set('Converter', 'output_same_dir', str(self._chk_same_dir.GetValue()))

        # Logging
        level_sel = self._choice_log_level.GetSelection()
        level = _LOG_LEVELS[level_sel] if level_sel != wx.NOT_FOUND else 'INFO'
        self._config.set('Logging', 'level', level)
        self._config.set('Logging', 'file_logging', str(self._chk_file_log.GetValue()))
        self._config.set('Logging', 'console_logging', str(self._chk_console_log.GetValue()))

        self._config.save()
        logger.info("Settings saved.")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_ok(self, event):
        self._save_values()
        event.Skip()

    def _on_browse_pandoc(self, _event):
        with wx.FileDialog(
            self,
            message=_("Locate pandoc executable"),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self._txt_pandoc_path.SetValue(dlg.GetPath())

    def _on_browse_outdir(self, _event):
        with wx.DirDialog(
            self,
            message=_("Choose default output directory"),
            style=wx.DD_DEFAULT_STYLE,
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self._txt_output_dir.SetValue(dlg.GetPath())
