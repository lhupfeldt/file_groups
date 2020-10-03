import re
from pathlib import Path

from file_groups.file_handler import FileHandler

from .conftest import same_content_files
from .utils.file_handler_test_utils import FP


# Matching patterns

@same_content_files('Hi', 'ki/x', 'df/y')
def test_rename_protected_source(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[re.compile('.*/y')])
    ck = FP(fh, str(Path('df/y').absolute()), 'df/z', capsys)
    assert not ck.check_rename(dry=True)
    assert not ck.check_rename(dry=False)

    out, _ = capsys.readouterr()
    assert f"NOT moving '{duplicates_dir}/df/y' protected by regex '.*/y' to 'df/z'." in out


@same_content_files('Hi', 'ki/x', 'df/y')
def test_move_protected_source(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[re.compile('.*/y')])
    ck = FP(fh, str(Path('df/y').absolute()), 'ki/z', capsys)
    assert not ck.check_move(dry=True)
    assert not ck.check_move(dry=False)

    out, _ = capsys.readouterr()
    assert f"NOT moving '{duplicates_dir}/df/y' protected by regex '.*/y' to 'ki/z'." in out


@same_content_files('Hi', 'ki/x', 'df/y')
def test_delete_protected_source(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[re.compile('.*/y')])
    ck = FP(fh, str(Path('df/y').absolute()), 'ki/x', capsys)
    assert not ck.check_delete(dry=True)
    assert not ck.check_delete(dry=False)

    out, _ = capsys.readouterr()
    assert f"NOT deleting '{duplicates_dir}/df/y' protected by regex '.*/y'." in out


@same_content_files('Hi', 'ki/x', 'df/y')
def test_rename_protected_target(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[re.compile('.*/z')])
    ck = FP(fh, str(Path('df/y').absolute()), 'df/z', capsys)
    assert not ck.check_rename(dry=True)
    assert not ck.check_rename(dry=False)

    out, _ = capsys.readouterr()
    assert f"NOT moving '{duplicates_dir}/df/y' to 'df/z' protected by regex '.*/z'." in out


@same_content_files('Hi', 'ki/x', 'df/y')
def test_move_protected_target(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[re.compile('.*/z')])
    ck = FP(fh, str(Path('df/y').absolute()), 'ki/z', capsys)
    assert not ck.check_move(dry=True)
    assert not ck.check_move(dry=False)

    out, _ = capsys.readouterr()
    assert f"NOT moving '{duplicates_dir}/df/y' to 'ki/z' protected by regex '.*/z'." in out


# Unmatched patterns


@same_content_files('Hi', 'ki/x', 'df/y')
def test_rename_unmatched_protection(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[re.compile('.*/NO')])
    ck = FP(fh, str(Path('df/y').absolute()), 'df/z', capsys)
    assert ck.check_rename(dry=True)
    assert ck.check_rename(dry=False)


@same_content_files('Hi', 'ki/x', 'df/y')
def test_move_unmatched_protection(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[re.compile('.*/NO')])
    ck = FP(fh, str(Path('df/y').absolute()), 'ki/z', capsys)
    assert ck.check_move(dry=True)
    assert ck.check_move(dry=False)


@same_content_files('Hi', 'ki/x', 'df/y')
def test_delete_unmatched_protection(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[re.compile('.*/NO')])
    ck = FP(fh, str(Path('df/y').absolute()), 'ki/x', capsys)
    assert ck.check_delete(dry=True)
    assert ck.check_delete(dry=False)
