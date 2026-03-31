"""
Helper functions and utilities
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional


def format_file_size(bytes_size: int) -> str:
    """
    Format file size in bytes to human-readable format.

    Args:
        bytes_size: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


def get_file_extension(filepath: str) -> str:
    """
    Get file extension (lowercase, without dot).

    Args:
        filepath: File path

    Returns:
        File extension
    """
    return Path(filepath).suffix.lower().lstrip('.')


def ensure_directory(directory: str) -> bool:
    """
    Ensure directory exists, create if not.

    Args:
        directory: Directory path

    Returns:
        True if directory exists or was created
    """
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory: {e}")
        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Invalid characters for Windows filenames
    invalid_chars = '<>:"/\\|?*'

    for char in invalid_chars:
        filename = filename.replace(char, '_')

    return filename


def truncate_string(text: str, max_length: int, suffix: str = '...') -> str:
    """
    Truncate string to maximum length.

    Args:
        text: Original text
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix
