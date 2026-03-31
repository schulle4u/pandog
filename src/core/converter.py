"""
Pandoc converter wrapper using subprocess
"""

import subprocess
from pathlib import Path
from typing import Optional

from config.defaults import FORMAT_EXTENSIONS
from utils.logger import get_logger

logger = get_logger('converter')


class PandocConverter:
    """Wraps pandoc as a subprocess. One instance is shared across the app."""

    def __init__(self, pandoc_path: str = 'pandoc'):
        self.pandoc_path = pandoc_path
        self._input_formats: Optional[list] = None
        self._output_formats: Optional[list] = None

    # ------------------------------------------------------------------
    # Format discovery
    # ------------------------------------------------------------------

    def get_input_formats(self) -> list:
        """Return list of supported input formats (cached)."""
        if self._input_formats is None:
            success, stdout, stderr = self._run(['--list-input-formats'])
            if success:
                self._input_formats = [f.strip() for f in stdout.splitlines() if f.strip()]
            else:
                logger.warning(f"Could not retrieve input formats: {stderr}")
                self._input_formats = []
        return self._input_formats

    def get_output_formats(self) -> list:
        """Return list of supported output formats (cached)."""
        if self._output_formats is None:
            success, stdout, stderr = self._run(['--list-output-formats'])
            if success:
                self._output_formats = [f.strip() for f in stdout.splitlines() if f.strip()]
            else:
                logger.warning(f"Could not retrieve output formats: {stderr}")
                self._output_formats = []
        return self._output_formats

    def invalidate_format_cache(self):
        """Clear cached format lists (call after pandoc_path change)."""
        self._input_formats = None
        self._output_formats = None

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def convert_file(
        self,
        input_file: str,
        output_file: str,
        input_fmt: str = '',
        output_fmt: str = '',
        extra_options: str = '',
    ) -> tuple:
        """
        Convert a single file via pandoc.

        Returns:
            (success: bool, stderr: str)
        """
        cmd = []
        if input_fmt:
            cmd += ['-f', input_fmt]
        if output_fmt:
            cmd += ['-t', output_fmt]
        cmd += ['-o', output_file, input_file]
        if extra_options.strip():
            cmd += extra_options.split()

        success, _, stderr = self._run(cmd)
        if success:
            logger.info(f"Converted: {input_file} -> {output_file}")
        else:
            logger.error(f"Conversion failed for {input_file}: {stderr}")
        return success, stderr

    def convert_text(
        self,
        text: str,
        output_file: str,
        input_fmt: str = 'markdown',
        output_fmt: str = 'html',
        extra_options: str = '',
    ) -> tuple:
        """
        Convert text (from stdin) to a file via pandoc.

        Returns:
            (success: bool, stderr: str)
        """
        cmd = []
        if input_fmt:
            cmd += ['-f', input_fmt]
        if output_fmt:
            cmd += ['-t', output_fmt]
        cmd += ['-o', output_file]
        if extra_options.strip():
            cmd += extra_options.split()

        try:
            result = subprocess.run(
                [self.pandoc_path] + cmd,
                input=text,
                capture_output=True,
                text=True,
                encoding='utf-8',
            )
            success = result.returncode == 0
            if success:
                logger.info(f"Text converted to: {output_file}")
            else:
                logger.error(f"Text conversion failed: {result.stderr}")
            return success, result.stderr
        except FileNotFoundError:
            msg = f"Pandoc not found at: {self.pandoc_path}"
            logger.error(msg)
            return False, msg
        except Exception as e:
            logger.error(f"Text conversion error: {e}")
            return False, str(e)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def build_output_path(self, input_file: str, output_fmt: str, output_dir: str = '') -> str:
        """
        Determine output file path.

        Args:
            input_file: Path to the input file
            output_fmt: Pandoc output format name
            output_dir: Target directory; uses input file's directory if empty

        Returns:
            Absolute path string for the output file
        """
        input_path = Path(input_file)
        ext = FORMAT_EXTENSIONS.get(output_fmt, output_fmt)
        stem = input_path.stem
        if output_dir:
            target_dir = Path(output_dir)
        else:
            target_dir = input_path.parent
        return str(target_dir / f"{stem}.{ext}")

    def is_available(self) -> bool:
        """Return True if pandoc can be executed."""
        success, _, _ = self._run(['--version'])
        return success

    def _run(self, args: list) -> tuple:
        """
        Run pandoc with given arguments.

        Returns:
            (success: bool, stdout: str, stderr: str)
        """
        try:
            result = subprocess.run(
                [self.pandoc_path] + args,
                creationflags=subprocess.CREATE_NO_WINDOW,
                capture_output=True,
                text=True,
                encoding='utf-8',
            )
            return result.returncode == 0, result.stdout, result.stderr
        except FileNotFoundError:
            msg = f"Pandoc not found at: {self.pandoc_path}"
            logger.error(msg)
            return False, '', msg
        except Exception as e:
            logger.error(f"Pandoc execution error: {e}")
            return False, '', str(e)
