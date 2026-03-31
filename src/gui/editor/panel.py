"""
Editor tab panel
"""

from pathlib import Path

import wx

from config.defaults import FORMAT_EXTENSIONS
from core.converter import PandocConverter
from utils.i18n import _
from utils.logger import get_logger

logger = get_logger('editor')


class EditorPanel(wx.Panel):
    """
    Tab panel for text editing and conversion.

    Provides a multi-line text editor. Text can be loaded from a file,
    edited freely, and saved as-is or converted via pandoc.
    The status bar is updated on every cursor movement/text change.
    """

    def __init__(self, parent, converter: PandocConverter, statusbar):
        super().__init__(parent)
        self.SetName('editor_panel')
        self._converter = converter
        self._statusbar = statusbar
        self._current_file: str = ''
        self._modified = False

        self._build_ui()
        self._modified = False  # Reset: TE_RICH2 fires EVT_TEXT during construction

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        main_sizer.Add(self._build_editor_section(), 1, wx.EXPAND | wx.ALL, 6)
        main_sizer.Add(self._build_conversion_section(), 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        self.SetSizer(main_sizer)

    def _build_editor_section(self) -> wx.Sizer:
        box = wx.StaticBox(self, label=_("Editor"))
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        panel = wx.Panel(box)
        panel.SetName('editor_section_panel')
        inner = wx.BoxSizer(wx.VERTICAL)

        self._text_ctrl = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_RICH2 | wx.HSCROLL,
        )
        self._text_ctrl.SetName('editor_text_ctrl')
        inner.Add(self._text_ctrl, 1, wx.EXPAND)

        panel.SetSizer(inner)
        sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 4)

        self._text_ctrl.Bind(wx.EVT_TEXT, self._on_text_changed)
        self._text_ctrl.Bind(wx.EVT_KEY_UP, self._on_key_up)
        self._text_ctrl.Bind(wx.EVT_LEFT_UP, self._on_mouse_up)
        self._text_ctrl.Bind(wx.EVT_CONTEXT_MENU, self._on_context_menu)

        return sizer

    def _build_conversion_section(self) -> wx.Sizer:
        box = wx.StaticBox(self, label=_("Conversion"))
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        panel = wx.Panel(box)
        panel.SetName('conversion_section_panel')
        row = wx.BoxSizer(wx.HORIZONTAL)

        lbl_fmt = wx.StaticText(panel, label=_("Output format:"))
        lbl_fmt.SetName('lbl_editor_output_format')
        self._choice_output = wx.Choice(panel)
        self._choice_output.SetName('choice_editor_output_format')

        self._btn_save = wx.Button(panel, label=_("&Save..."))
        self._btn_save.SetName('btn_editor_save')
        self._btn_save_as = wx.Button(panel, label=_("Save &As..."))
        self._btn_save_as.SetName('btn_editor_save_as')

        row.Add(lbl_fmt, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        row.Add(self._choice_output, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        row.AddStretchSpacer()
        row.Add(self._btn_save, 0, wx.RIGHT, 4)
        row.Add(self._btn_save_as, 0)

        panel.SetSizer(row)
        sizer.Add(panel, 0, wx.EXPAND | wx.ALL, 4)

        self._btn_save.Bind(wx.EVT_BUTTON, self._on_save)
        self._btn_save_as.Bind(wx.EVT_BUTTON, self._on_save_as)

        return sizer

    # ------------------------------------------------------------------
    # Format loading
    # ------------------------------------------------------------------

    def load_output_formats(self, formats: list):
        """Populate output format choice (called by notebook after converter init)."""
        self._choice_output.Clear()
        for fmt in formats:
            self._choice_output.Append(fmt)
        if 'html' in formats:
            self._choice_output.SetSelection(formats.index('html'))
        elif formats:
            self._choice_output.SetSelection(0)

    def reload_formats(self, formats: list):
        """Re-populate formats after pandoc path change."""
        self.load_output_formats(formats)

    # ------------------------------------------------------------------
    # Public API (menu bar integration)
    # ------------------------------------------------------------------

    def new_document(self):
        if self._check_unsaved():
            self._text_ctrl.SetValue('')
            self._current_file = ''
            self._modified = False
            self._update_statusbar_info()

    def open_file(self, path: str):
        """Load a file into the editor."""
        try:
            text = Path(path).read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                text = Path(path).read_text(encoding='latin-1')
            except Exception as e:
                wx.MessageBox(
                    _("Could not read file:\n") + str(e),
                    _("Error"),
                    wx.OK | wx.ICON_ERROR,
                    self,
                )
                return
        except Exception as e:
            wx.MessageBox(
                _("Could not read file:\n") + str(e),
                _("Error"),
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return

        self._text_ctrl.SetValue(text)
        self._current_file = path
        self._modified = False
        self._update_statusbar_info()
        logger.info(f"Opened file in editor: {path}")

    def save_file(self) -> bool:
        """Save to current file. Opens Save As dialog if no file is set."""
        if self._current_file:
            return self._write_plain(self._current_file)
        return self._show_save_as_dialog()

    def get_text(self) -> str:
        return self._text_ctrl.GetValue()

    def is_modified(self) -> bool:
        return self._modified

    def check_unsaved(self) -> bool:
        """Returns True if it is safe to proceed (no unsaved changes or user confirmed)."""
        return self._check_unsaved()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_text_changed(self, _event):
        self._modified = True
        self._update_statusbar_info()

    def _on_key_up(self, event):
        self._update_statusbar_info()
        event.Skip()

    def _on_mouse_up(self, event):
        self._update_statusbar_info()
        event.Skip()

    def _on_save(self, _event):
        self.save_file()

    def _on_save_as(self, _event):
        self.show_save_as_dialog()

    def _on_context_menu(self, _event):
        tc = self._text_ctrl
        has_selection = bool(tc.GetStringSelection())
        can_undo = tc.CanUndo()
        can_redo = tc.CanRedo()
        can_paste = tc.CanPaste()

        menu = wx.Menu()

        item_undo = menu.Append(wx.ID_UNDO, _("&Undo"))
        item_undo.Enable(can_undo)
        item_redo = menu.Append(wx.ID_REDO, _("&Redo"))
        item_redo.Enable(can_redo)
        menu.AppendSeparator()
        item_cut = menu.Append(wx.ID_CUT, _("Cu&t"))
        item_cut.Enable(has_selection)
        item_copy = menu.Append(wx.ID_COPY, _("&Copy"))
        item_copy.Enable(has_selection)
        item_paste = menu.Append(wx.ID_PASTE, _("&Paste"))
        item_paste.Enable(can_paste)
        item_delete = menu.Append(wx.ID_DELETE, _("&Delete"))
        item_delete.Enable(has_selection)
        menu.AppendSeparator()
        menu.Append(wx.ID_SELECTALL, _("Select &all"))

        menu.Bind(wx.EVT_MENU, lambda e: tc.Undo(), item_undo)
        menu.Bind(wx.EVT_MENU, lambda e: tc.Redo(), item_redo)
        menu.Bind(wx.EVT_MENU, lambda e: tc.Cut(), item_cut)
        menu.Bind(wx.EVT_MENU, lambda e: tc.Copy(), item_copy)
        menu.Bind(wx.EVT_MENU, lambda e: tc.Paste(), item_paste)
        menu.Bind(wx.EVT_MENU, lambda e: tc.Remove(*tc.GetSelection()), item_delete)
        menu.Bind(wx.EVT_MENU, lambda e: tc.SelectAll(), id=wx.ID_SELECTALL)

        self.PopupMenu(menu)
        menu.Destroy()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _show_save_as_dialog(self) -> bool:
        output_fmt = self._get_selected_format()
        ext = FORMAT_EXTENSIONS.get(output_fmt, output_fmt) if output_fmt else '*'
        if ext and ext != '*':
            wildcard = f"{output_fmt} (*.{ext})|*.{ext}|{_('All files')} (*.*)|*.*"
        else:
            wildcard = f"{_('All files')} (*.*)|*.*"
        with wx.FileDialog(
            self,
            message=_("Save as"),
            wildcard=wildcard,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return False
            path = dlg.GetPath()
            # Append extension if the user didn't type one and a format is selected
            if ext and ext != '*' and not path.lower().endswith(f'.{ext}'):
                path += f'.{ext}'

        if output_fmt and output_fmt not in ('plain', 'native'):
            # Convert via pandoc
            success, stderr = self._converter.convert_text(
                self._text_ctrl.GetValue(), path, output_fmt=output_fmt
            )
            if not success:
                wx.MessageBox(
                    _("Conversion failed:\n") + stderr,
                    _("Error"),
                    wx.OK | wx.ICON_ERROR,
                    self,
                )
                return False
        else:
            if not self._write_plain(path):
                return False

        self._current_file = path
        self._modified = False
        logger.info(f"Saved editor content to: {path}")
        return True

    def _write_plain(self, path: str) -> bool:
        try:
            Path(path).write_text(self._text_ctrl.GetValue(), encoding='utf-8')
            self._modified = False
            return True
        except Exception as e:
            wx.MessageBox(
                _("Could not save file:\n") + str(e),
                _("Error"),
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return False

    def _get_selected_format(self) -> str:
        sel = self._choice_output.GetSelection()
        if sel == wx.NOT_FOUND:
            return ''
        return self._choice_output.GetString(sel)

    def _check_unsaved(self) -> bool:
        """Prompt if there are unsaved changes. Returns True if safe to proceed."""
        if not self._modified:
            return True
        # No file open and editor is empty → nothing to lose (e.g. spurious EVT_TEXT
        # fired by TE_RICH2 during theme application or widget initialisation)
        if not self._current_file and not self._text_ctrl.GetValue():
            return True
        answer = wx.MessageBox(
            _("There are unsaved changes. Discard them?"),
            _("Unsaved changes"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
            self,
        )
        return answer == wx.YES

    def _update_statusbar_info(self):
        text = self._text_ctrl.GetValue()
        insertion = self._text_ctrl.GetInsertionPoint()
        # Calculate line and column from insertion point
        text_before = text[:insertion]
        lines = text_before.split('\n')
        line = len(lines)
        col = len(lines[-1]) + 1
        chars = len(text)
        words = len(text.split()) if text.strip() else 0
        self._statusbar.set_editor_info(line, col, chars, words)
