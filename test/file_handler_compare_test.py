from pathlib import Path

from file_groups.compare_files import CompareFiles
from file_groups.handler_compare import FileHandlerCompare

from .conftest import same_content_files, different_content_files
from .utils.file_handler_test_utils import FP


# TODO: output

@same_content_files('Hi', 'ki/x', 'df/y')
def test_file_handler_compare_duplicate_files(duplicates_dir):
    fh = FileHandlerCompare(['ki'], ['df'], CompareFiles(), dry_run=True, protected_regexes=[])
    assert fh.compare('df/y', 'ki/x')
    fh.dry_run = False
    assert fh.compare(Path('df/y'), Path('ki/x'))


@different_content_files("oops", 'df/f11', 'ki/f12')
def test_file_handler_compare_different_files(duplicates_dir):
    fh = FileHandlerCompare(['ki'], ['df'], CompareFiles(), dry_run=True, protected_regexes=[])
    assert not fh.compare(Path('df/f11'), Path('ki/f12'))
    fh.dry_run = False
    assert not fh.compare(Path('df/f11'), Path('ki/f12'))


@same_content_files('Hi', 'ki/x', 'df/y')
def test_file_handler_compare_duplicate_moved_files(duplicates_dir, log_debug):
    fh = FileHandlerCompare(['ki'], ['df'], CompareFiles(), dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/y').absolute()), 'ki/z', log_debug)
    ck.check_move(dry=True)
    assert fh.compare(Path('ki/x'), Path('ki/z'))
    ck.check_move(dry=False)
    assert fh.compare(Path('ki/x'), Path('ki/z'))


@different_content_files("oops", 'ki/x', 'df/y')
def test_file_handler_compare_different_moved_files(duplicates_dir, log_debug):
    fh = FileHandlerCompare(['ki'], ['df'], CompareFiles(), dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/y').absolute()), 'ki/z', log_debug)
    ck.check_move(dry=True)
    assert not fh.compare(Path('ki/x'), Path('ki/z'))
    ck.check_move(dry=False)
    assert not fh.compare(Path('ki/x'), Path('ki/z'))
