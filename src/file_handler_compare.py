from __future__ import annotations

import os
from pathlib import Path
import re
from typing import Sequence

from .compare_files import CompareFiles
from .types import FsPath
from .file_handler import FileHandler


class FileHandlerCompare(FileHandler):
    """Extend `FileHandler` with a compare method

    Arguments:
        protect_dirs_seq, work_dirs_seq, protect_exclude, work_include, debug: See `FileGroups` class.
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
            delete_symlinks_instead_of_relinking=False,
            debug=False):
        super().__init__(
            protect_dirs_seq=protect_dirs_seq,
            work_dirs_seq=work_dirs_seq,
            dry_run=dry_run,
            protected_regexes=protected_regexes,
            protect_exclude=protect_exclude,
            work_include=work_include,
            delete_symlinks_instead_of_relinking=delete_symlinks_instead_of_relinking,
            debug=debug)

        self._fcmp = fcmp

    def compare(self, f1: FsPath, f2: FsPath) -> bool:
        """Extends CompareFiles.compare with logic to handle 'renamed/moved' files during dry_run."""

        if not self.dry_run:
            if self._fcmp.compare(f1, f2):
                print(f"Duplicates: '{f1}' '{f2}'")
                return True

            return False

        f1_abs = str(Path(f1).absolute())
        existing_f1 = Path(self.moved_from.get(os.fspath(f1_abs), f1))
        f2_abs = str(Path(f2).absolute())
        existing_f2 = Path(self.moved_from.get(os.fspath(f2_abs), f2))
        if self._fcmp.compare(existing_f1, existing_f2):
            print(f"Duplicates: '{f1}' '{f2}'")
            return True

        return False
