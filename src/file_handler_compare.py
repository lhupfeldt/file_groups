from __future__ import annotations

import os
from pathlib import Path
import re
import logging
from typing import Sequence

from .compare_files import CompareFiles
from .types import FsPath
from .file_handler import FileHandler


_LOG = logging.getLogger(__name__)


class FileHandlerCompare(FileHandler):
    """Extend `FileHandler` with a compare method

    Arguments:
        protect_dirs_seq, work_dirs_seq, protect_exclude, work_include: See `FileGroups` class.
        dry_run, protected_regexes, delete_symlinks_instead_of_relinking: See `FileHandler` class.
        fcmp: Object providing compare function.
    """

    def __init__(
            self,
            protect_dirs_seq: Sequence[Path], work_dirs_seq: Sequence[Path], fcmp: CompareFiles,
            *,
            dry_run: bool,
            protected_regexes: Sequence[re.Pattern],
            protect_exclude: re.Pattern|None = None, work_include: re.Pattern|None = None,
            delete_symlinks_instead_of_relinking=False):
        super().__init__(
            protect_dirs_seq=protect_dirs_seq,
            work_dirs_seq=work_dirs_seq,
            dry_run=dry_run,
            protected_regexes=protected_regexes,
            protect_exclude=protect_exclude,
            work_include=work_include,
            delete_symlinks_instead_of_relinking=delete_symlinks_instead_of_relinking)

        self._fcmp = fcmp

    def compare(self, fsp1: FsPath, fsp2: FsPath) -> bool:
        """Extends CompareFiles.compare with logic to handle 'renamed/moved' files during dry_run."""

        if not self.dry_run:
            if self._fcmp.compare(fsp1, fsp2):
                _LOG.info("Duplicates: '%s' '%s'", fsp1, fsp2)
                return True

            return False

        fsp1_abs = str(Path(fsp1).absolute())
        existing_fsp1 = Path(self.moved_from.get(os.fspath(fsp1_abs), fsp1))
        fsp2_abs = str(Path(fsp2).absolute())
        existing_fsp2 = Path(self.moved_from.get(os.fspath(fsp2_abs), fsp2))
        if self._fcmp.compare(existing_fsp1, existing_fsp2):
            _LOG.info("Duplicates: '%s' '%s'", fsp1, fsp2)
            return True

        return False
