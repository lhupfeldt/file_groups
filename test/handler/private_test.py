"""Test some FileHandler internals."""

import re
from pathlib import Path

import pytest

from file_groups.handler import FileHandler

from ..conftest import same_content_files


# pylint: disable=protected-access

@same_content_files('Hi', 'y')
def test_no_symlink_check_registered_delete_ok(duplicates_dir, log_debug):
    fh = FileHandler([], '.', dry_run=False, protected_regexes=[])

    y_abs = str(Path('y').absolute())
    fh._no_symlink_check_registered_delete(y_abs)

    assert f"deleting: {y_abs}" in log_debug.text
    assert not Path('y').exists()


@same_content_files('Hi', 'y')
def test_no_symlink_check_registered_delete_ok_dry(duplicates_dir, log_debug):
    fh = FileHandler([], '.', dry_run=True, protected_regexes=[])

    y_abs = str(Path('y').absolute())
    fh._no_symlink_check_registered_delete(y_abs)

    print(fh.moved_from)
    assert f"deleting: {y_abs}" in log_debug.text
    assert Path('y').exists()


@same_content_files('Hi', 'ya')
def test_no_symlink_check_registered_delete_ok_protected_matched(duplicates_dir, log_debug):
    fh = FileHandler([], '.', dry_run=False, protected_regexes=[re.compile(r'.*a$')])

    ya_abs = str(Path('ya').absolute())
    with pytest.raises(AssertionError) as exinfo:
        fh._no_symlink_check_registered_delete(ya_abs)

    assert f"Oops, trying to delete protected file '{str(ya_abs)}'." in str(exinfo.value)

    exp_msg = f"find MAY_WORK_ON - '{duplicates_dir}/ya' is protected by regex re.compile('.*a$'), assigning to group MUST_PROTECT instead."
    assert exp_msg in log_debug.text
    assert Path(ya_abs).exists()


@same_content_files('Hi', 'ya')
def test_no_symlink_check_registered_delete_ok_dry_protected_matched(duplicates_dir):
    fh = FileHandler([], '.', dry_run=True, protected_regexes=[re.compile(r'.*a$')])

    ya_abs = str(Path('ya').absolute())
    with pytest.raises(AssertionError) as exinfo:
        fh._no_symlink_check_registered_delete(ya_abs)

    assert f"Oops, trying to delete protected file '{str(ya_abs)}'." in str(exinfo.value)
    assert Path(ya_abs).exists()


@same_content_files('Hi', 'ya')
def test_no_symlink_check_registered_delete_ok_protected_un_matched(duplicates_dir, log_debug):
    fh = FileHandler([], '.', dry_run=False, protected_regexes=[re.compile(r'.*b$')])

    ya_abs = str(Path('ya').absolute())
    fh._no_symlink_check_registered_delete(ya_abs)

    assert f"deleting: {ya_abs}" in log_debug.text
    assert not Path('ya').exists()


@same_content_files('Hi', 'ya')
def test_no_symlink_check_registered_delete_ok_dry_protected_un_matched(duplicates_dir, log_debug):
    fh = FileHandler([], '.', dry_run=True, protected_regexes=[re.compile(r'.*b$')])

    ya_abs = str(Path('ya').absolute())
    fh._no_symlink_check_registered_delete(ya_abs)

    assert f"deleting: {ya_abs}" in log_debug.text
    assert Path('ya').exists()
