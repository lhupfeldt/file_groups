import sys
import traceback
from pathlib import Path
from dataclasses import dataclass

import pytest

from file_groups.handler import FileHandler


@dataclass
class FP():
    """File Pair.

    Methods to check dry/do_it delete, move and rename with the same pair of files.

    left, right are filenames/paths
    """

    fh: FileHandler
    left: str
    right: str
    capture: pytest.fixture

    def check_rename(self, dry, rename_or_move='renaming', is_overwrite=False) -> Path|bool:
        self.fh.dry_run = dry
        self.fh.reset()
        if rename_or_move == 'renaming':
            res = self.fh.registered_rename(self.left, self.right)
        else:
            res = self.fh.registered_move(self.left, self.right)

        try:
            # caplog obj
            out = self.capture.text
        except AttributeError:
            # capsys obj
            out, _ = self.capture.readouterr()
        print(out)

        try:
            if rename_or_move == 'renaming':
                assert self.fh.num_renamed >= 1
            else:
                assert self.fh.num_moved >= 1

            assert f"{rename_or_move}: {self.left}" in out

            if dry:
                assert Path(self.left).exists()
                assert is_overwrite or not Path(self.right).exists()
            else:
                assert not Path(self.left).exists()
                assert Path(self.right).exists()

            assert res, f"Expected a Path as result, got: {res}"
        except AssertionError as ex:
            print(ex)
            traceback.print_exception(*sys.exc_info())
            return False

        return res

    def check_move(self, dry, is_overwrite=False):
        return self.check_rename(dry, rename_or_move='moving', is_overwrite=is_overwrite)

    def check_delete(self, dry) -> Path|bool:
        self.fh.dry_run = dry
        self.fh.reset()
        res = self.fh.registered_delete(self.left, self.right)

        try:
            # capsys obj
            out, _ = self.capture.readouterr()
        except AttributeError:
            # caplog obj
            out = self.capture.text
            self.capture.clear()
        print(out)

        try:
            assert self.fh.num_deleted >= 1
            assert f"deleting: {self.left}" in out
            if dry:
                assert Path(self.left).exists()
                assert self.right is None or Path(self.right).exists()
            else:
                assert not Path(self.left).exists()
                assert self.right is None or Path(self.right).exists()

            if self.right is not None:
                assert res, f"Expected a Path as result, got: {res}"
                return res
        except AssertionError as ex:
            print(ex)
            traceback.print_exception(*sys.exc_info())
            return False

        return True
