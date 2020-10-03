"""Test some FileHandler internals."""

import re
from pathlib import Path

from file_groups.file_handler import FileHandler

from .conftest import same_content_files


# pylint: disable=protected-access

@same_content_files('Hi', 'y')
def test_no_symlink_check_registered_delete_ok(duplicates_dir, capsys):
    fh = FileHandler([], '.', None, dry_run=False, protected_regexes=[])

    y_abs = str(Path('y').absolute())
    assert fh._no_symlink_check_registered_delete(y_abs)

    out, _ = capsys.readouterr()
    assert f"deleting: {y_abs}" in out

    assert not Path('y').exists()


@same_content_files('Hi', 'y')
def test_no_symlink_check_registered_delete_ok_dry(duplicates_dir, capsys):
    fh = FileHandler([], '.', None, dry_run=True, protected_regexes=[])

    y_abs = str(Path('y').absolute())
    assert fh._no_symlink_check_registered_delete(y_abs)

    out, _ = capsys.readouterr()
    print(fh.moved_from)
    assert f"deleting: {y_abs}" in out

    assert Path('y').exists()


@same_content_files('Hi', 'ya')
def test_no_symlink_check_registered_delete_ok_protected_matched(duplicates_dir, capsys):
    fh = FileHandler([], '.', None, dry_run=False, protected_regexes=[re.compile(r'.*a$')])

    ya_abs = str(Path('ya').absolute())
    assert not fh._no_symlink_check_registered_delete(ya_abs)

    out, _ = capsys.readouterr()
    assert f"NOT deleting '{ya_abs}' protected by regex '.*a$'." in out

    assert Path(ya_abs).exists()


@same_content_files('Hi', 'ya')
def test_no_symlink_check_registered_delete_ok_dry_protected_matched(duplicates_dir, capsys):
    fh = FileHandler([], '.', None, dry_run=True, protected_regexes=[re.compile(r'.*a$')])

    ya_abs = str(Path('ya').absolute())
    assert not fh._no_symlink_check_registered_delete(ya_abs)

    out, _ = capsys.readouterr()
    assert f"NOT deleting '{ya_abs}' protected by regex '.*a$'." in out

    assert Path(ya_abs).exists()


@same_content_files('Hi', 'ya')
def test_no_symlink_check_registered_delete_ok_protected_un_matched(duplicates_dir, capsys):
    fh = FileHandler([], '.', None, dry_run=False, protected_regexes=[re.compile(r'.*b$')])

    ya_abs = str(Path('ya').absolute())
    assert fh._no_symlink_check_registered_delete(ya_abs)

    out, _ = capsys.readouterr()
    assert f"deleting: {ya_abs}" in out

    assert not Path('ya').exists()


@same_content_files('Hi', 'ya')
def test_no_symlink_check_registered_delete_ok_dry_protected_un_matched(duplicates_dir, capsys):
    fh = FileHandler([], '.', None, dry_run=True, protected_regexes=[re.compile(r'.*b$')])

    ya_abs = str(Path('ya').absolute())
    assert fh._no_symlink_check_registered_delete(ya_abs)

    out, _ = capsys.readouterr()
    assert f"deleting: {ya_abs}" in out

    assert Path('ya').exists()
