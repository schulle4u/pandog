"""
PanDoG – Entry point
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import wx

from config.config_manager import ConfigManager
from utils.i18n import initialize_i18n
from utils.logger import configure_logging, get_logger


def main():
    # Bootstrap configuration
    config = ConfigManager()

    # Configure logging from config
    configure_logging(
        level=config.get('Logging', 'level', fallback='INFO'),
        file_logging=config.getboolean('Logging', 'file_logging', fallback=True),
        console_logging=config.getboolean('Logging', 'console_logging', fallback=False),
    )

    logger = get_logger('main')
    logger.info("PanDoG starting up.")

    # Initialise i18n
    lang = config.get('General', 'language', fallback=None)
    initialize_i18n(lang if lang else None)

    # wx imports require wx.App to exist first, so import GUI here
    app = wx.App(redirect=False)

    from gui.main_window import MainFrame
    from gui.theme_manager import ThemeManager
    theme_manager = ThemeManager(config)

    frame = MainFrame(config, theme_manager)
    frame.Show()

    logger.info("Entering main loop.")
    app.MainLoop()


if __name__ == '__main__':
    main()
