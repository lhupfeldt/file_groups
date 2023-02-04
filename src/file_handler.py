from __future__ import annotations

import os
from pathlib import Path
import shutil
import re
from contextlib import contextmanager
from typing import Sequence

from .compare_files import CompareFiles
from .types import FsPath
from .file_groups import FileGroups


class FileHandler(FileGroups):
    """Protected files and symlinks safe operations on files in FileGroups.

    Check that files being deleted/renamed/moved are not in the protect files set and that files in protect files are not overwritten.
    Re-link symlinks pointing to a file being moved.
    Re-link symlinks when a file being deleted has a corresponding file.

    Arguments:
        protect_dirs_seq, work_dirs_seq, protect_exclude, work_include, debug: See `FileGroups` class.
        dry_run: Don't actually do anything.
        protected_regexes: Protect files matching this from being deleted or moved.
        delete_symlinks_instead_of_relinking: Normal operation is to re-link to a 'corresponding' or renamed file when renaming or deleting a file.
           If delete_symlinks_instead_of_relinking is true, then symlinks in work_on dirs pointing to renamed/deletes files will be deleted even if
           they could have logically been made to point to a file in a protect dir.
        debug: Be very verbose.
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
            protect=protected_regexes,
            protect_dirs_seq=protect_dirs_seq, work_dirs_seq=work_dirs_seq,
            protect_exclude=protect_exclude, work_include=work_include,
            debug=debug)

        self._fcmp = fcmp

        self.dry_run = dry_run
        self.delete_symlinks_instead_of_relinking = delete_symlinks_instead_of_relinking

        # Holds paths of deleted symlinks
        self.deleted_symlinks: set[str] = set()

        # Set to point to path of original file when 'registered_move' or 'registered_rename' is called during dry_run
        self.moved_from: dict[str, str] = {}

        self.num_deleted = 0
        self.num_renamed = 0
        self.num_moved = 0
        self.num_relinked = 0

    def reset(self):
        """Reset internal housekeeping of deleted/renamed/moved files.

        This makes it possible to do a 'dry_run' and an actual run without collecting files again.
        """

        self.deleted_symlinks = set()
        self.moved_from = {}

        self.num_deleted = 0
        self.num_renamed = 0
        self.num_moved = 0
        self.num_relinked = 0

    def trace(self, *args, **kwargs):
        if self.debug:
            print(*args, **kwargs)

    def _no_symlink_check_registered_delete(self, delete_path: str):
        """Does a registered delete without checking for symlinks, so that we can use this in the symlink handling."""
        assert isinstance(delete_path, str)
        assert os.path.isabs(delete_path), f"Expected absolute path, got '{delete_path}'"
        assert delete_path not in self.must_protect.files, f"Oops, trying to delete protected file '{delete_path}'."
        assert delete_path not in self.must_protect.symlinks, f"Oops, trying to delete protected symlink '{delete_path}'."

        print("    deleting:", delete_path)
        if not self.dry_run:
            os.unlink(delete_path)
        self.num_deleted += 1

        if delete_path in self.may_work_on.symlinks:
            self.deleted_symlinks.add(delete_path)

    def _handle_single_symlink_chain(self, symlnk_path: str, keep_path):
        """TODO doc - Symlink will only be deleted if it is in self.may_work_on.files."""

        assert os.path.isabs(symlnk_path), f"Expected an absolute path, got '{symlnk_path}'"

        if symlnk_path in self.deleted_symlinks:
            self.trace(f"{symlnk_path} previously deleted.")
            return

        points_to = os.readlink(symlnk_path)
        abs_points_to = os.path.normpath(os.path.join(os.path.dirname(symlnk_path), points_to))

        # Check whether symlink points outside our work files
        if abs_points_to not in self.may_work_on.files and abs_points_to not in self.may_work_on.symlinks:
            print(f"Keeping symlink pointing outside delete-dirs: '{symlnk_path}' -> '{points_to}' ({abs_points_to})")
            return

        print(f"Symlinked: '{symlnk_path}' -> '{points_to}' ({abs_points_to})")

        if self.delete_symlinks_instead_of_relinking or not keep_path:
            # Find symlinks to the symlink which we will delete, and delete those as well
            symlnk_to_symlinks = self.may_work_on.symlinks_by_abs_points_to.get(symlnk_path, [])
            for symlnk_to_symlink in symlnk_to_symlinks:
                abs_points_to_symlnk = os.path.normpath(os.path.join(os.path.dirname(symlnk_to_symlink), symlnk_to_symlink))
                print(f"Symlink to symlink: '{symlnk_to_symlink}' ({abs_points_to_symlnk}).")
                self._handle_single_symlink_chain(abs_points_to_symlnk, keep_path)

        if self.delete_symlinks_instead_of_relinking and (symlnk_path in self.may_work_on.files or symlnk_path in self.may_work_on.symlinks):
            self._no_symlink_check_registered_delete(symlnk_path)
            return

        if not keep_path:
            if symlnk_path in self.may_work_on.files or symlnk_path in self.may_work_on.symlinks:
                self._no_symlink_check_registered_delete(symlnk_path)
            else:
                # TODO
                print("Created broken symlink '{points_from}' -> '{points_to}'")
            return

        abs_keep_path = Path(keep_path).absolute()
        abs_keep_dir = os.path.dirname(abs_keep_path)
        abs_symlnk_dir = os.path.dirname(symlnk_path)
        if abs_keep_dir == abs_symlnk_dir:
            keep_path = os.path.basename(keep_path)
        else:
            try:
                keep_path = abs_keep_path.relative_to(abs_symlnk_dir)
            except ValueError:
                keep_path = abs_keep_path

        print(f"Changing symlink: '{symlnk_path}' -> '{keep_path}' (was -> {points_to})")
        if not self.dry_run:
            os.unlink(symlnk_path)
            os.symlink(keep_path, symlnk_path)

        self.num_relinked += 1

    def _fix_symlinks_to_deleted_or_moved_files(self, from_path: str, to_path):
        """Any symlinks pointing to 'from_path' will be change to point to 'to_path'"""
        self.trace(f"_fix_symlinks_to_deleted_or_moved_files(self, {from_path}, {to_path})")

        for symlnk in self.must_protect.symlinks_by_abs_points_to.get(from_path, ()):
            self.trace(f"_fix_symlinks_to_deleted_or_moved_files, must protect symlink: '{symlnk}'.")
            self._handle_single_symlink_chain(os.fspath(symlnk), to_path)

        for symlnk in self.may_work_on.symlinks_by_abs_points_to.get(from_path, ()):
            self.trace(f"_fix_symlinks_to_deleted_or_moved_files, may_work_on symlink: '{symlnk}'.")
            self._handle_single_symlink_chain(os.fspath(symlnk), to_path)

    def registered_delete(self, delete_path: str, corresponding_keep_path):
        self._no_symlink_check_registered_delete(delete_path)
        self._fix_symlinks_to_deleted_or_moved_files(delete_path, corresponding_keep_path)

    def _registered_move_or_rename(self, from_path: str, to_path, *, is_move):
        assert isinstance(from_path, str)
        assert os.path.isabs(from_path), f"Expected absolute path, got '{from_path}'"
        assert from_path not in self.must_protect.files, f"Oops, trying to move/rename protected file '{from_path}'."
        assert from_path not in self.must_protect.symlinks, f"Oops, trying to move/rename protected symlink '{from_path}'."
        abs_tp = str(Path(to_path).absolute())
        assert abs_tp not in self.must_protect.files, f"Oops, trying to overwrite protected file '{Path(to_path).absolute()}' with '{from_path}'."
        assert abs_tp not in self.must_protect.symlinks, f"Oops, trying to overwrite protected symlink '{to_path}' with '{from_path}'."

        tp = os.fspath(to_path)

        if self.dry_run:
            self.moved_from[abs_tp] = from_path

        if is_move:
            print("    moving:", from_path, 'to', tp)
            if not self.dry_run:
                shutil.move(from_path, to_path)

            self.num_moved += 1
        else:
            print("    renaming:", from_path, 'to', tp)
            if not self.dry_run:
                os.rename(from_path, to_path)

            self.num_renamed += 1

        self._fix_symlinks_to_deleted_or_moved_files(from_path, to_path)

    def registered_move(self, from_path: str, to_path):
        self._registered_move_or_rename(from_path, to_path, is_move=True)

    def registered_rename(self, from_path: str, to_path):
        self._registered_move_or_rename(from_path, to_path, is_move=False)

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

    @contextmanager
    def stats(self):
        prefix = ''

        print()
        if self.dry_run:
            print("*** DRY RUN ***")
            prefix = 'would have '

        super().stats()
        print()
        print(f'{prefix}deleted:', self.num_deleted)
        print(f'{prefix}renamed:', self.num_renamed)
        print(f'{prefix}moved:', self.num_moved)
        print(f'{prefix}relinked:', self.num_relinked)

        try:
            yield

        finally:
            if self.dry_run:
                print("*** DRY RUN ***")
