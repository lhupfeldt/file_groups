"""Test some FileHandler internals."""

import re
from pathlib import Path

import pytest

from file_groups.file_handler import FileHandler

from .conftest import same_content_files


# pylint: disable=protected-access

@same_content_files('Hi', 'y')
def test_no_symlink_check_registered_delete_ok(duplicates_dir, capsys):
    fh = FileHandler([], '.', dry_run=False, protected_regexes=[])

    y_abs = str(Path('y').absolute())
    fh._no_symlink_check_registered_delete(y_abs)

    out, _ = capsys.readouterr()
    assert f"deleting: {y_abs}" in out

    assert not Path('y').exists()


@same_content_files('Hi', 'y')
def test_no_symlink_check_registered_delete_ok_dry(duplicates_dir, capsys):
    fh = FileHandler([], '.', dry_run=True, protected_regexes=[])

    y_abs = str(Path('y').absolute())
    fh._no_symlink_check_registered_delete(y_abs)

    out, _ = capsys.readouterr()
    print(fh.moved_from)
    assert f"deleting: {y_abs}" in out

    assert Path('y').exists()


@same_content_files('Hi', 'ya')
def test_no_symlink_check_registered_delete_ok_protected_matched(duplicates_dir, capsys):
    fh = FileHandler([], '.', dry_run=False, protected_regexes=[re.compile(r'.*a$')], debug=True)

    ya_abs = str(Path('ya').absolute())
    with pytest.raises(AssertionError) as exinfo:
        fh._no_symlink_check_registered_delete(ya_abs)

    assert f"Oops, trying to delete protected file '{str(ya_abs)}'." in str(exinfo.value)

    out, _ = capsys.readouterr()
    exp_msg = f"find MAY_WORK_ON - '{duplicates_dir}/ya' is protected by regex re.compile('.*a$'), assigning to group MUST_PROTECT instead."
    assert exp_msg in out

    assert Path(ya_abs).exists()


@same_content_files('Hi', 'ya')
def test_no_symlink_check_registered_delete_ok_dry_protected_matched(duplicates_dir, capsys):
    fh = FileHandler([], '.', dry_run=True, protected_regexes=[re.compile(r'.*a$')])

    ya_abs = str(Path('ya').absolute())
    with pytest.raises(AssertionError) as exinfo:
        fh._no_symlink_check_registered_delete(ya_abs)

    assert f"Oops, trying to delete protected file '{str(ya_abs)}'." in str(exinfo.value)

    assert Path(ya_abs).exists()


@same_content_files('Hi', 'ya')
def test_no_symlink_check_registered_delete_ok_protected_un_matched(duplicates_dir, capsys):
    fh = FileHandler([], '.', dry_run=False, protected_regexes=[re.compile(r'.*b$')])

    ya_abs = str(Path('ya').absolute())
    fh._no_symlink_check_registered_delete(ya_abs)

    out, _ = capsys.readouterr()
    assert f"deleting: {ya_abs}" in out

    assert not Path('ya').exists()


@same_content_files('Hi', 'ya')
def test_no_symlink_check_registered_delete_ok_dry_protected_un_matched(duplicates_dir, capsys):
    fh = FileHandler([], '.', dry_run=True, protected_regexes=[re.compile(r'.*b$')])

    ya_abs = str(Path('ya').absolute())
    fh._no_symlink_check_registered_delete(ya_abs)

    out, _ = capsys.readouterr()
    assert f"deleting: {ya_abs}" in out

    assert Path('ya').exists()
