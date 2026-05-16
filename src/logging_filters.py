"""Change logging of Path objects."""

from logging import Filter
import logging
from typing import Any

from .path_display import PathDisplay
from .config.dir_config import DirConfig


class PathFilter(PathDisplay, Filter):
    """Logging filter to change how paths are logged.

    E.g. Log relative paths or show home dir as '~'.
    Handle logging of DirEntry.
    """

    def __init__(self, *, home_tilde: bool, rel_path: bool):
        super().__init__(home_tilde=home_tilde, rel_path=rel_path)

        if self.home_tilde or self.rel_path:
            self.filter = self._do_filter  # type: ignore
            return

        self.filter = self._no_filter  # type: ignore

    def _do_filter(self, record: logging.LogRecord) -> bool:
        """Log user's home dir of Path objects as '~'."""
        if record.args:
            record.args = self.handle_any(record.args)

        return True

    def _no_filter(self, record: logging.LogRecord) -> bool:  # pylint: disable=unused-argument
        return True

    def handle_any(self, arg: Any) -> Any:
        match arg:
            case DirConfig():
                # TODO, create new DirConfig with path corrected?
                return self.handle_str(str(arg), count=-1)

        return super().handle_any(arg)
