"""
Configuration Manager for PanDoG
Handles loading and saving configuration files with portable mode support
"""

import os
import sys
import configparser
from pathlib import Path
from typing import Any, Dict

from config.defaults import DEFAULT_CONFIG


class ConfigManager:
    """Manages application configuration with portable mode support"""

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_path = self._determine_config_path()
        self._load_config()

    def _determine_config_path(self) -> Path:
        """
        Determine configuration file path based on portable mode.

        Portable mode: config.ini in program directory
        Normal mode: Platform-specific user config directory
        """
        # Get program directory
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            program_dir = Path(sys.executable).parent
        else:
            # Running as script
            program_dir = Path(__file__).parent.parent.parent

        portable_config = program_dir / 'config.ini'

        # Check for portable mode
        if portable_config.exists():
            return portable_config

        # Use platform-specific user config directory
        if sys.platform == 'win32':
            config_dir = Path(os.environ.get('APPDATA', '~')) / 'PanDoG'
        elif sys.platform == 'darwin':
            config_dir = Path.home() / 'Library' / 'Application Support' / 'PanDoG'
        else:  # Linux and others
            config_dir = Path.home() / '.config' / 'pandog'

        # Create config directory if it doesn't exist
        config_dir.mkdir(parents=True, exist_ok=True)

        return config_dir / 'config.ini'

    def _load_config(self):
        """Load configuration from file or create with defaults"""
        if self.config_path.exists():
            try:
                self.config.read(self.config_path, encoding='utf-8')
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
                self._set_defaults()
        else:
            self._set_defaults()
            self.save()

    def _set_defaults(self):
        """Set default configuration values"""
        for section, options in DEFAULT_CONFIG.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            for key, value in options.items():
                self.config.set(section, key, str(value))

    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, section: str, option: str, fallback: Any = None) -> str:
        """Get configuration value"""
        return self.config.get(section, option, fallback=fallback)

    def getint(self, section: str, option: str, fallback: int = 0) -> int:
        """Get configuration value as integer"""
        return self.config.getint(section, option, fallback=fallback)

    def getfloat(self, section: str, option: str, fallback: float = 0.0) -> float:
        """Get configuration value as float"""
        return self.config.getfloat(section, option, fallback=fallback)

    def getboolean(self, section: str, option: str, fallback: bool = False) -> bool:
        """Get configuration value as boolean"""
        return self.config.getboolean(section, option, fallback=fallback)

    def set(self, section: str, option: str, value: Any):
        """Set configuration value"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, str(value))

    def get_all(self, section: str) -> Dict[str, str]:
        """Get all options in a section as dictionary"""
        if self.config.has_section(section):
            return dict(self.config.items(section))
        return {}

    # Recent Files Management

    def get_recent_files(self) -> list:
        """
        Get list of recent files.

        Returns:
            List of recent file paths (most recent first)
        """
        recent = []
        max_items = self.getint('Recent', 'max_recent_items', 10)

        if not self.config.has_section('RecentFiles'):
            return recent

        for i in range(1, max_items + 1):
            key = f'file_{i}'
            if self.config.has_option('RecentFiles', key):
                path = self.config.get('RecentFiles', key)
                if path:
                    recent.append(path)

        return recent

    def add_recent_file(self, filepath: str):
        """
        Add a file to the recent files list.

        Args:
            filepath: Path to file or URL
        """
        if not filepath:
            return

        # Get current list
        recent = self.get_recent_files()

        # Remove if already in list (to move to top)
        if filepath in recent:
            recent.remove(filepath)

        # Add to beginning
        recent.insert(0, filepath)

        # Limit to max items
        max_items = self.getint('Recent', 'max_recent_items', 10)
        recent = recent[:max_items]

        # Save to config
        self._save_recent_files(recent)

    def remove_recent_file(self, filepath: str):
        """
        Remove a file from the recent files list.

        Args:
            filepath: Path to file to remove
        """
        recent = self.get_recent_files()
        if filepath in recent:
            recent.remove(filepath)
            self._save_recent_files(recent)

    def clear_recent_files(self):
        """Clear all recent files"""
        if self.config.has_section('RecentFiles'):
            self.config.remove_section('RecentFiles')
        self.config.add_section('RecentFiles')
        self.save()

    def _save_recent_files(self, recent: list):
        """Save recent files list to config"""
        # Clear existing
        if self.config.has_section('RecentFiles'):
            self.config.remove_section('RecentFiles')
        self.config.add_section('RecentFiles')

        # Save new list
        for i, path in enumerate(recent, start=1):
            self.config.set('RecentFiles', f'file_{i}', path)

        self.save()


