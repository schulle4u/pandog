"""
Converter tab panel
"""

import threading
from pathlib import Path

import wx

from core.converter import PandocConverter
from utils.i18n import _
from utils.helpers import format_file_size


class ConverterPanel(wx.Panel):
    """
    Tab panel for file conversion.

    Allows the user to add one or more files, select input/output formats,
    configure an output directory, and start the pandoc conversion.
    Conversion runs in a background thread so the UI remains responsive.
    """

    def __init__(self, parent, converter: PandocConverter, statusbar, on_files_added=None):
        super().__init__(parent)
        self.SetName('converter_panel')
        self._converter = converter
        self._statusbar = statusbar
        self._files: list = []  # list of absolute path strings
        self._on_files_added = on_files_added  # optional callback(paths: list)

        self._build_ui()
        self._load_formats()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        main_sizer.Add(self._build_file_section(), 1, wx.EXPAND | wx.ALL, 6)
        main_sizer.Add(self._build_options_section(), 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)
        main_sizer.Add(self._build_action_section(), 0, wx.ALIGN_RIGHT | wx.ALL, 6)

        self.SetSizer(main_sizer)

    def _build_file_section(self) -> wx.Sizer:
        box = wx.StaticBox(self, label=_("Files"))
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        panel = wx.Panel(box)
        panel.SetName('file_section_panel')
        inner = wx.BoxSizer(wx.VERTICAL)

        # File list
        self._file_list = wx.ListCtrl(
            panel,
            style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_VRULES,
        )
        self._file_list.SetName('file_list')
        self._file_list.InsertColumn(0, _("Filename"), width=220)
        self._file_list.InsertColumn(1, _("Size"), width=80)
        self._file_list.InsertColumn(2, _("Directory"), width=300)
        inner.Add(self._file_list, 1, wx.EXPAND | wx.BOTTOM, 4)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._btn_add = wx.Button(panel, label=_("&Add files..."))
        self._btn_add.SetName('btn_add_files')
        self._btn_add_dir = wx.Button(panel, label=_("Add &directory..."))
        self._btn_add_dir.SetName('btn_add_directory')
        self._btn_remove = wx.Button(panel, label=_("&Remove"))
        self._btn_remove.SetName('btn_remove_file')
        self._btn_remove.Disable()
        self._btn_clear = wx.Button(panel, label=_("Clear &list"))
        self._btn_clear.SetName('btn_clear_list')
        self._btn_clear.Disable()

        btn_sizer.Add(self._btn_add, 0, wx.RIGHT, 4)
        btn_sizer.Add(self._btn_add_dir, 0, wx.RIGHT, 4)
        btn_sizer.Add(self._btn_remove, 0, wx.RIGHT, 4)
        btn_sizer.Add(self._btn_clear)
        inner.Add(btn_sizer, 0)

        panel.SetSizer(inner)
        sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 4)

        # Events
        self._btn_add.Bind(wx.EVT_BUTTON, self._on_add_files)
        self._btn_add_dir.Bind(wx.EVT_BUTTON, self._on_add_directory)
        self._btn_remove.Bind(wx.EVT_BUTTON, self._on_remove_file)
        self._btn_clear.Bind(wx.EVT_BUTTON, self._on_clear_list)
        self._file_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_list_selection_changed)
        self._file_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self._on_list_selection_changed)

        return sizer

    def _build_options_section(self) -> wx.Sizer:
        box = wx.StaticBox(self, label=_("Conversion options"))
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        panel = wx.Panel(box)
        panel.SetName('options_section_panel')
        grid = wx.FlexGridSizer(rows=0, cols=2, vgap=6, hgap=8)
        grid.AddGrowableCol(1)

        # Input format
        lbl_in = wx.StaticText(panel, label=_("Input format:"))
        lbl_in.SetName('lbl_input_format')
        self._choice_input = wx.Choice(panel)
        self._choice_input.SetName('choice_input_format')
        grid.Add(lbl_in, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self._choice_input, 1, wx.EXPAND)

        # Output format
        lbl_out = wx.StaticText(panel, label=_("Output format:"))
        lbl_out.SetName('lbl_output_format')
        self._choice_output = wx.Choice(panel)
        self._choice_output.SetName('choice_output_format')
        grid.Add(lbl_out, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self._choice_output, 1, wx.EXPAND)

        # Output directory
        lbl_dir = wx.StaticText(panel, label=_("Output directory:"))
        lbl_dir.SetName('lbl_output_dir')
        dir_row = wx.BoxSizer(wx.HORIZONTAL)
        self._txt_output_dir = wx.TextCtrl(panel)
        self._txt_output_dir.SetName('txt_output_dir')
        self._btn_browse_dir = wx.Button(panel, label=_("&Browse..."))
        self._btn_browse_dir.SetName('btn_browse_output_dir')
        dir_row.Add(self._txt_output_dir, 1, wx.EXPAND | wx.RIGHT, 4)
        dir_row.Add(self._btn_browse_dir, 0)
        grid.Add(lbl_dir, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(dir_row, 1, wx.EXPAND)

        # Same-dir checkbox (spans both columns)
        self._chk_same_dir = wx.CheckBox(panel, label=_("Use same directory as input file"))
        self._chk_same_dir.SetName('chk_same_dir')
        self._chk_same_dir.SetValue(True)
        grid.Add((0, 0))  # empty first column
        grid.Add(self._chk_same_dir, 0)

        # Extra pandoc options
        lbl_opts = wx.StaticText(panel, label=_("Extra options:"))
        lbl_opts.SetName('lbl_extra_options')
        self._txt_extra_opts = wx.TextCtrl(panel)
        self._txt_extra_opts.SetName('txt_extra_options')
        grid.Add(lbl_opts, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self._txt_extra_opts, 1, wx.EXPAND)

        panel.SetSizer(grid)
        sizer.Add(panel, 0, wx.EXPAND | wx.ALL, 4)

        # Events
        self._chk_same_dir.Bind(wx.EVT_CHECKBOX, self._on_same_dir_toggled)
        self._btn_browse_dir.Bind(wx.EVT_BUTTON, self._on_browse_dir)
        self._on_same_dir_toggled(None)  # sync initial state

        return sizer

    def _build_action_section(self) -> wx.Sizer:
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._btn_convert = wx.Button(self, label=_("&Convert"))
        self._btn_convert.SetName('btn_convert')
        self._btn_convert.Disable()
        sizer.Add(self._btn_convert)
        self._btn_convert.Bind(wx.EVT_BUTTON, self._on_convert)
        return sizer

    # ------------------------------------------------------------------
    # Format loading
    # ------------------------------------------------------------------

    def _load_formats(self):
        """Populate format choices from pandoc at startup."""
        input_formats = self._converter.get_input_formats()
        output_formats = self._converter.get_output_formats()

        # Prepend empty entry (auto-detect)
        auto = _("(auto-detect)")
        self._choice_input.Append(auto)
        for fmt in input_formats:
            self._choice_input.Append(fmt)
        self._choice_input.SetSelection(0)

        self._choice_output.Append(auto)
        for fmt in output_formats:
            self._choice_output.Append(fmt)
        # Select default output format
        default_out = 'html'
        if default_out in output_formats:
            self._choice_output.SetSelection(output_formats.index(default_out) + 1)
        else:
            self._choice_output.SetSelection(0)

    def reload_formats(self):
        """Re-fetch formats after a pandoc path change."""
        self._converter.invalidate_format_cache()
        self._choice_input.Clear()
        self._choice_output.Clear()
        self._load_formats()

    # ------------------------------------------------------------------
    # Public helpers (called from menu)
    # ------------------------------------------------------------------

    def add_files(self, paths: list):
        """Add files to the list (also callable from menu bar)."""
        added = []
        for path in paths:
            if path not in self._files:
                self._files.append(path)
                added.append(path)
                p = Path(path)
                size_str = format_file_size(p.stat().st_size) if p.exists() else ''
                idx = self._file_list.GetItemCount()
                self._file_list.InsertItem(idx, p.name)
                self._file_list.SetItem(idx, 1, size_str)
                self._file_list.SetItem(idx, 2, str(p.parent))
        self._update_button_states()
        if added and self._on_files_added:
            self._on_files_added(added)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_add_files(self, _event):
        with wx.FileDialog(
            self,
            message=_("Add files"),
            style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.add_files(dlg.GetPaths())

    def _on_add_directory(self, _event):
        with wx.DirDialog(
            self,
            message=_("Add directory"),
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            directory = dlg.GetPath()

        answer = wx.MessageBox(
            _("Include files from subdirectories?"),
            _("Add directory"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
            self,
        )
        recursive = (answer == wx.YES)
        files = self._collect_files_from_dir(directory, recursive)
        if files:
            self.add_files(files)
        else:
            wx.MessageBox(
                _("No files found in the selected directory."),
                _("Add directory"),
                wx.OK | wx.ICON_INFORMATION,
                self,
            )

    def _on_remove_file(self, _event):
        selected = self._file_list.GetFirstSelected()
        while selected != -1:
            self._file_list.DeleteItem(selected)
            self._files.pop(selected)
            selected = self._file_list.GetFirstSelected()
        self._update_button_states()

    def _on_clear_list(self, _event):
        self._file_list.DeleteAllItems()
        self._files.clear()
        self._update_button_states()

    def _on_list_selection_changed(self, _event):
        self._update_button_states()

    def _on_same_dir_toggled(self, _event):
        use_same = self._chk_same_dir.GetValue()
        self._txt_output_dir.Enable(not use_same)
        self._btn_browse_dir.Enable(not use_same)

    def _on_browse_dir(self, _event):
        with wx.DirDialog(
            self,
            message=_("Choose output directory"),
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self._txt_output_dir.SetValue(dlg.GetPath())

    def _on_convert(self, _event):
        if not self._files:
            return

        input_fmt = self._get_selected_format(self._choice_input)
        output_fmt = self._get_selected_format(self._choice_output)
        use_same_dir = self._chk_same_dir.GetValue()
        output_dir = '' if use_same_dir else self._txt_output_dir.GetValue().strip()
        extra_opts = self._txt_extra_opts.GetValue().strip()

        if not output_fmt:
            wx.MessageBox(
                _("Please select an output format."),
                _("No output format"),
                wx.OK | wx.ICON_WARNING,
                self,
            )
            return

        self._btn_convert.Disable()
        self._statusbar.set_converter_status(_("Converting…"))

        files = list(self._files)
        thread = threading.Thread(
            target=self._run_conversion,
            args=(files, input_fmt, output_fmt, output_dir, extra_opts),
            daemon=True,
        )
        thread.start()

    # ------------------------------------------------------------------
    # Background conversion
    # ------------------------------------------------------------------

    def _run_conversion(self, files, input_fmt, output_fmt, output_dir, extra_opts):
        errors = []
        for path in files:
            out_path = self._converter.build_output_path(path, output_fmt, output_dir)
            success, stderr = self._converter.convert_file(
                path, out_path, input_fmt, output_fmt, extra_opts
            )
            if not success:
                errors.append(f"{Path(path).name}: {stderr.strip()}")

        wx.CallAfter(self._on_conversion_done, errors)

    def _on_conversion_done(self, errors):
        self._btn_convert.Enable()
        if errors:
            msg = "\n\n".join(errors)
            self._statusbar.set_converter_status(_("Conversion finished with errors"))
            wx.MessageBox(
                _("Some files could not be converted:\n\n") + msg,
                _("Conversion errors"),
                wx.OK | wx.ICON_ERROR,
                self,
            )
        else:
            n = len(self._files)
            self._statusbar.set_converter_status(
                _("{n} file(s) converted successfully").format(n=n)
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _collect_files_from_dir(self, directory: str, recursive: bool) -> list:
        """Return a sorted list of file paths from the given directory."""
        root = Path(directory)
        pattern = '**/*' if recursive else '*'
        return sorted(
            str(p) for p in root.glob(pattern)
            if p.is_file()
        )

    def _get_selected_format(self, choice: wx.Choice) -> str:
        """Return the selected format string, or '' for the auto-detect entry."""
        sel = choice.GetSelection()
        if sel <= 0:
            return ''
        return choice.GetString(sel)

    def _update_button_states(self):
        has_files = len(self._files) > 0
        has_selection = self._file_list.GetSelectedItemCount() > 0
        self._btn_remove.Enable(has_selection)
        self._btn_clear.Enable(has_files)
        self._btn_convert.Enable(has_files)
