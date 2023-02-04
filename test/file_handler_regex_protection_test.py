import sys
import re
from pathlib import Path

import pytest

from file_groups.file_handler import FileHandler

from .conftest import same_content_files
from .utils.file_handler_test_utils import FP


# Matching patterns


def check_protected_source(action, dupe_dir, capsys):
    try:
        fh = FileHandler(['ki'], ['df'], dry_run=True, protected_regexes=[re.compile('.*/y')])
        ck = FP(fh, str(Path('df/y').absolute()), 'df/z', capsys)

        action_msg = action if action == 'delete' else "move/rename"

        with pytest.raises(AssertionError) as exinfo:
            getattr(ck, 'check_' + action)(dry=True)
        assert f"Oops, trying to {action_msg} protected file '{dupe_dir}/df/y'." in str(exinfo.value)

        with pytest.raises(AssertionError) as exinfo:
            getattr(ck, 'check_' + action)(dry=False)
        assert f"Oops, trying to {action_msg} protected file '{dupe_dir}/df/y'." in str(exinfo.value)

        assert Path(dupe_dir/'ki/x').exists()
        assert Path(dupe_dir/'df/y').exists()
    except AssertionError as ex:
        print(ex, sys.stderr, flush=True)
        return False

    return True


@same_content_files('Hi', 'ki/x', 'df/y')
def test_rename_protected_source(duplicates_dir, capsys):
    assert check_protected_source('rename', duplicates_dir, capsys)


@same_content_files('Hi', 'ki/x', 'df/y')
def test_move_protected_source(duplicates_dir, capsys):
    assert check_protected_source('move', duplicates_dir, capsys)


@same_content_files('Hi', 'ki/x', 'df/y')
def test_delete_protected_source(duplicates_dir, capsys):
    assert check_protected_source('delete', duplicates_dir, capsys)


@same_content_files('Hi', 'ki/x', 'df/y', 'df/z')
def test_rename_protected_target(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], dry_run=True, protected_regexes=[re.compile('.*/z')])
    ck = FP(fh, str(Path('df/y').absolute()), 'df/z', capsys)

    with pytest.raises(AssertionError) as exinfo:
        ck.check_rename(dry=True)

    exp = f"Oops, trying to overwrite protected file '{duplicates_dir}/df/z' with '{duplicates_dir}/df/y'."
    assert exp in str(exinfo.value)

    with pytest.raises(AssertionError) as exinfo:
        ck.check_rename(dry=False)
    exp = f"Oops, trying to overwrite protected file '{duplicates_dir}/df/z' with '{duplicates_dir}/df/y'."
    assert exp in str(exinfo.value)

    assert Path(duplicates_dir/'df/y').exists()
    assert Path(duplicates_dir/'df/z').exists()


@same_content_files('Hi', 'ki/x', 'df/y', 'df/z')
def test_move_protected_target(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], dry_run=True, protected_regexes=[re.compile('.*/z')])
    ck = FP(fh, str(Path('df/y').absolute()), 'df/z', capsys)

    with pytest.raises(AssertionError) as exinfo:
        ck.check_move(dry=True)
    exp = f"Oops, trying to overwrite protected file '{duplicates_dir}/df/z' with '{duplicates_dir}/df/y'."
    assert exp in str(exinfo.value)

    with pytest.raises(AssertionError) as exinfo:
        ck.check_move(dry=False)
    exp = f"Oops, trying to overwrite protected file '{duplicates_dir}/df/z' with '{duplicates_dir}/df/y'."
    assert exp in str(exinfo.value)

    assert Path(duplicates_dir/'df/y').exists()
    assert Path(duplicates_dir/'df/z').exists()


@same_content_files('Hi', 'ki/x', 'df/y')
def test_rename_protected_target_pattern_bu_no_target_file(duplicates_dir, capsys):
    """It is allowed to move to a target file matching a protect regex if the file does not exist."""
    fh = FileHandler(['ki'], ['df'], dry_run=True, protected_regexes=[re.compile('.*/z')])
    ck = FP(fh, str(Path('df/y').absolute()), 'df/z', capsys)

    assert ck.check_rename(dry=True)
    assert ck.check_rename(dry=False)

    assert Path(duplicates_dir/'df/z').exists()
    assert not Path(duplicates_dir/'df/y').exists()


@same_content_files('Hi', 'ki/x', 'df/y')
def test_move_protected_target_pattern_bu_no_target_file(duplicates_dir, capsys):
    """It is allowed to move to a target file matching a protect regex if the file does not exist."""
    fh = FileHandler(['ki'], ['df'], dry_run=True, protected_regexes=[re.compile('.*/z')])
    ck = FP(fh, str(Path('df/y').absolute()), 'df/z', capsys)

    assert ck.check_move(dry=True)
    assert ck.check_move(dry=False)

    assert Path(duplicates_dir/'df/z').exists()
    assert not Path(duplicates_dir/'df/y').exists()


# Unmatched patterns


@same_content_files('Hi', 'ki/x', 'df/y')
def test_rename_unmatched_protection(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], dry_run=True, protected_regexes=[re.compile('.*/NO')])
    ck = FP(fh, str(Path('df/y').absolute()), 'df/z', capsys)
    assert ck.check_rename(dry=True)
    assert ck.check_rename(dry=False)


@same_content_files('Hi', 'ki/x', 'df/y')
def test_move_unmatched_protection(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], dry_run=True, protected_regexes=[re.compile('.*/NO')])
    ck = FP(fh, str(Path('df/y').absolute()), 'ki/z', capsys)
    assert ck.check_move(dry=True)
    assert ck.check_move(dry=False)


@same_content_files('Hi', 'ki/x', 'df/y')
def test_delete_unmatched_protection(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], dry_run=True, protected_regexes=[re.compile('.*/NO')])
    ck = FP(fh, str(Path('df/y').absolute()), 'ki/x', capsys)
    assert ck.check_delete(dry=True)
    assert ck.check_delete(dry=False)
