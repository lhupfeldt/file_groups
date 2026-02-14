import os
import re
from pathlib import Path
import logging
from dataclasses import dataclass
from typing import Any

from ..types import FsPath


_LOG = logging.getLogger(__name__)


@dataclass
class RecursiveConfig():
    """Hold global (site or user) protect config."""
    protect_recursive: set[re.Pattern]

    def __json__(self) -> dict[str, Any]:
        return {
            RecursiveConfig.__name__: {
                "protect_recursive": [str(pat) for pat in self.protect_recursive],
            }
        }


@dataclass
class DirConfig(RecursiveConfig):
    """Hold directory specific protect config."""
    protect_local: set[re.Pattern]
    config_dir: Path|None
    config_files: list[str]

    def __post_init__(self) -> None:
        """Both local and  recursive protections are protected locally."""
        self._protected = self.protect_local | self.protect_recursive

    def is_protected(self, ff: FsPath) -> re.Pattern|None:
        """If ff id protected by a regex pattern then return the pattern, otherwise return None."""

        # _LOG.debug("ff '%s'", ff)
        for pattern in self._protected:
            if os.sep in str(pattern):
                # _LOG.debug("re.Pattern '%s' has path sep", pattern)
                assert os.path.isabs(ff), f"Expected absolute path, got '{ff}'"

                # Search against full path
                if pattern.search(os.fspath(ff)):
                    return pattern

                # Attempt exact match against path relative to , i.e. if pattern starts with '^'.
                # This makes sense for patterns specified on commandline
                cwd = os.getcwd()
                ff_relative = str(Path(ff).relative_to(cwd))
                # _LOG.debug("ff '%s' relative to start dir'%s'", ff_relative, cwd)

                if pattern.match(ff_relative):
                    return pattern

            elif pattern.search(ff.name):
                return pattern

        return None

    def __json__(self) -> dict[str, Any]:
        return {
            DirConfig.__name__: super().__json__()[RecursiveConfig.__name__] | {
                "protect_local": [str(pat) for pat in self.protect_local],
                "config_dir": str(self.config_dir),
                "config_files": self.config_files,
            }
        }
