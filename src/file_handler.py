from __future__ import annotations

import os
from pathlib import Path
import shutil
import re
from contextlib import contextmanager
import logging
from typing import Sequence

from .file_groups import FileGroups


_LOG = logging.getLogger(__name__)


class FileHandler(FileGroups):
    """Protected files and symlinks safe operations on files in FileGroups.

    Check that files being deleted/renamed/moved are not in the protect files set and that files in protect files are not overwritten.
    Re-link symlinks pointing to a file being moved.
    Re-link symlinks when a file being deleted has a corresponding file.

    Arguments:
        protect_dirs_seq, work_dirs_seq, protect_exclude, work_include: See `FileGroups` class.
        dry_run: Don't actually do anything.
        protected_regexes: Protect files matching this from being deleted or moved.
        delete_symlinks_instead_of_relinking: Normal operation is to re-link to a 'corresponding' or renamed file when renaming or deleting a file.
           If delete_symlinks_instead_of_relinking is true, then symlinks in work_on dirs pointing to renamed/deletes files will be deleted even if
           they could have logically been made to point to a file in a protect dir.
    """

    def __init__(
            self,
            protect_dirs_seq: Sequence[Path], work_dirs_seq: Sequence[Path],
            *,
            dry_run: bool,
            protected_regexes: Sequence[re.Pattern],
            protect_exclude: re.Pattern|None = None, work_include: re.Pattern|None = None,
            delete_symlinks_instead_of_relinking=False):
        super().__init__(
            protect=protected_regexes,
            protect_dirs_seq=protect_dirs_seq, work_dirs_seq=work_dirs_seq,
            protect_exclude=protect_exclude, work_include=work_include)

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

    def _no_symlink_check_registered_delete(self, delete_path: str):
        """Does a registered delete without checking for symlinks, so that we can use this in the symlink handling."""
        assert isinstance(delete_path, str)
        assert os.path.isabs(delete_path), f"Expected absolute path, got '{delete_path}'"
        assert delete_path not in self.must_protect.files, f"Oops, trying to delete protected file '{delete_path}'."
        assert delete_path not in self.must_protect.symlinks, f"Oops, trying to delete protected symlink '{delete_path}'."

        _LOG.info("    deleting: %s", delete_path)
        if not self.dry_run:
            os.unlink(delete_path)
        self.num_deleted += 1

        if delete_path in self.may_work_on.symlinks:
            self.deleted_symlinks.add(delete_path)

    def _handle_single_symlink_chain(self, symlnk_path: str, keep_path):
        """TODO doc - Symlink will only be deleted if it is in self.may_work_on.files."""

        assert os.path.isabs(symlnk_path), f"Expected an absolute path, got '{symlnk_path}'"

        if symlnk_path in self.deleted_symlinks:
            _LOG.debug("%s previously deleted.", symlnk_path)
            return

        points_to = os.readlink(symlnk_path)
        abs_points_to = os.path.normpath(os.path.join(os.path.dirname(symlnk_path), points_to))

        # Check whether symlink points outside our work files
        if abs_points_to not in self.may_work_on.files and abs_points_to not in self.may_work_on.symlinks:
            _LOG.info("Keeping symlink pointing outside delete-dirs: '%s' -> '%s' (%s)", symlnk_path, points_to, abs_points_to)
            return

        _LOG.info("Symlinked: '%s' -> '%s' (%s)", symlnk_path, points_to, abs_points_to)

        if self.delete_symlinks_instead_of_relinking or not keep_path:
            # Find symlinks to the symlink which we will delete, and delete those as well
            symlnk_to_symlinks = self.may_work_on.symlinks_by_abs_points_to.get(symlnk_path, [])
            for symlnk_to_symlink in symlnk_to_symlinks:
                abs_points_to_symlnk = os.path.normpath(os.path.join(os.path.dirname(symlnk_to_symlink), symlnk_to_symlink))
                _LOG.info("Symlink to symlink: '%s' (%s).", symlnk_to_symlink, abs_points_to_symlnk)
                self._handle_single_symlink_chain(abs_points_to_symlnk, keep_path)

        if self.delete_symlinks_instead_of_relinking and (symlnk_path in self.may_work_on.files or symlnk_path in self.may_work_on.symlinks):
            self._no_symlink_check_registered_delete(symlnk_path)
            return

        if not keep_path:
            if symlnk_path in self.may_work_on.files or symlnk_path in self.may_work_on.symlinks:
                self._no_symlink_check_registered_delete(symlnk_path)
            else:
                # TODO, verify message
                _LOG.info("Created broken symlink '%s' -> '%s'", symlnk_path, points_to)
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

        _LOG.info("Changing symlink: '%s' -> '%s' (was -> %s)", symlnk_path, keep_path, points_to)
        if not self.dry_run:
            os.unlink(symlnk_path)
            os.symlink(keep_path, symlnk_path)

        self.num_relinked += 1

    def _fix_symlinks_to_deleted_or_moved_files(self, from_path: str, to_path):
        """Any symlinks pointing to 'from_path' will be change to point to 'to_path'"""
        _LOG.debug("_fix_symlinks_to_deleted_or_moved_files(self, %s, %s)", from_path, to_path)

        for symlnk in self.must_protect.symlinks_by_abs_points_to.get(from_path, ()):
            _LOG.debug("_fix_symlinks_to_deleted_or_moved_files, must protect symlink: '%s'.", symlnk)
            self._handle_single_symlink_chain(os.fspath(symlnk), to_path)

        for symlnk in self.may_work_on.symlinks_by_abs_points_to.get(from_path, ()):
            _LOG.debug("_fix_symlinks_to_deleted_or_moved_files, may_work_on symlink: '%s'.", symlnk)
            self._handle_single_symlink_chain(os.fspath(symlnk), to_path)

    def registered_delete(self, delete_path: str, corresponding_keep_path) -> Path|None:
        """Return `corresponding_keep_path` as absolute Path"""
        self._no_symlink_check_registered_delete(delete_path)
        self._fix_symlinks_to_deleted_or_moved_files(delete_path, corresponding_keep_path)
        return Path(corresponding_keep_path).absolute() if corresponding_keep_path else None

    def _registered_move_or_rename(self, from_path: str, to_path, *, is_move) -> Path:
        """Return `to_path` as absolute Path"""
        assert isinstance(from_path, str)
        assert os.path.isabs(from_path), f"Expected absolute path, got '{from_path}'"
        assert from_path not in self.must_protect.files, f"Oops, trying to move/rename protected file '{from_path}'."
        assert from_path not in self.must_protect.symlinks, f"Oops, trying to move/rename protected symlink '{from_path}'."
        res = Path(to_path).absolute()
        abs_tp = str(res)
        assert abs_tp not in self.must_protect.files, f"Oops, trying to overwrite protected file '{Path(to_path).absolute()}' with '{from_path}'."
        assert abs_tp not in self.must_protect.symlinks, f"Oops, trying to overwrite protected symlink '{to_path}' with '{from_path}'."

        if self.dry_run:
            self.moved_from[abs_tp] = from_path

        if is_move:
            _LOG.info("    moving: %s to %s", from_path, os.fspath(to_path))
            if not self.dry_run:
                shutil.move(from_path, to_path)

            self.num_moved += 1
        else:
            _LOG.info("    renaming: %s to %s", from_path, os.fspath(to_path))
            if not self.dry_run:
                os.rename(from_path, to_path)

            self.num_renamed += 1

        self._fix_symlinks_to_deleted_or_moved_files(from_path, to_path)
        return res

    def registered_move(self, from_path: str, to_path) -> Path:
        """Return `to_path` as absolute Path"""
        return self._registered_move_or_rename(from_path, to_path, is_move=True)

    def registered_rename(self, from_path: str, to_path) -> Path:
        """Return `to_path` as absolute Path"""
        return self._registered_move_or_rename(from_path, to_path, is_move=False)

    @contextmanager
    def stats(self):
        log = _LOG.getChild("stats")
        lvl = logging.INFO
        if not log.isEnabledFor(lvl):
            yield
            return

        prefix = ''

        log.log(lvl, "")
        if self.dry_run:
            log.log(lvl, "*** DRY RUN ***")
            prefix = 'would have '

        super().stats()
        log.log(lvl, "")
        log.log(lvl, "%sdeleted: %s", prefix, self.num_deleted)
        log.log(lvl, "%srenamed: %s", prefix, self.num_renamed)
        log.log(lvl, "%smoved: %s", prefix, self.num_moved)
        log.log(lvl, "%srelinked: %s", prefix, self.num_relinked)

        try:
            yield

        finally:
            if self.dry_run:
                log.log(lvl, "*** DRY RUN ***")
