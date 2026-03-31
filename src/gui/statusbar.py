"""
Status bar for PanDoG main window
"""

import wx

from utils.i18n import _


class AppStatusBar(wx.StatusBar):
    """
    Three-field status bar:
      Field 0 – general application status
      Field 1 – converter status
      Field 2 – editor info (line/col/word count)
    """

    _FIELD_STATUS = 0
    _FIELD_CONVERTER = 1
    _FIELD_EDITOR = 2

    def __init__(self, parent):
        super().__init__(parent, style=wx.STB_DEFAULT_STYLE)
        self.SetName('status_bar')
        self.SetFieldsCount(3)
        self.SetStatusWidths([-2, -2, -3])
        self.set_status(_("Ready"))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_status(self, message: str):
        """Update the general status field."""
        self.SetStatusText(message, self._FIELD_STATUS)

    def set_converter_status(self, message: str):
        """Update the converter status field."""
        self.SetStatusText(message, self._FIELD_CONVERTER)

    def set_editor_info(self, line: int, col: int, chars: int, words: int):
        """Update the editor info field."""
        text = _("Ln {line}, Col {col}  |  {chars} chars, {words} words").format(
            line=line, col=col, chars=chars, words=words
        )
        self.SetStatusText(text, self._FIELD_EDITOR)

    def clear_editor_info(self):
        """Clear the editor info field."""
        self.SetStatusText('', self._FIELD_EDITOR)

    def clear_converter_status(self):
        """Clear the converter status field."""
        self.SetStatusText('', self._FIELD_CONVERTER)
