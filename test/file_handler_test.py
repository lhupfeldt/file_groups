import os
from pathlib import Path

import pytest

from file_groups.file_handler import FileHandler

from .conftest import same_content_files, symlink_files, count_files
from .utils.file_handler_test_utils import FP


@same_content_files('Hi', 'ki/x', 'df/y')
def test_rename_no_symlinks(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/y').absolute()), 'df/z', capsys)
    assert ck.check_rename(dry=True)
    assert ck.check_rename(dry=False)


@same_content_files('Hi', 'ki/x', 'df/y')
def test_move_no_symlinks(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/y').absolute()), 'ki/z', capsys)
    assert ck.check_move(dry=True)
    assert ck.check_move(dry=False)


@same_content_files('Hi', 'ki/x', 'df/y')
def test_delete_no_symlinks_with_corresponding(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/y').absolute()), 'ki/x', capsys)
    assert ck.check_delete(dry=True)
    assert ck.check_delete(dry=False)


@same_content_files('Hi', 'ki/x', 'df/y')
def test_delete_no_symlinks_without_corresponding(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/y').absolute()), None, capsys)
    assert ck.check_delete(dry=True)
    assert ck.check_delete(dry=False)


# Test existing to_path


@same_content_files('Hi', 'ki/ttt', 'df/z', 'df/y')
def test_rename_existing_to_path(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/y').absolute()), 'df/z', capsys)
    ck.check_rename(dry=True)
    ck.check_rename(dry=False)
    pytest.xfail("TODO: overwrite check for overwriting 'work_on' file?")


@same_content_files('Hi', 'outside/a', 'ki/z', 'df/y')
def test_move_existing_to_path(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/y').absolute()), 'ki/z', capsys)
    with pytest.raises(AssertionError):
        ck.check_move(dry=True)
    with pytest.raises(AssertionError):
        ck.check_move(dry=False)

    ck = FP(fh, str(Path('df/y').absolute()), 'outside/a', capsys)
    ck.check_move(dry=True)
    ck.check_move(dry=False)
    pytest.xfail("TODO: overwrite check for run overwriting file outside groups?")


# Operations on files symlinked to once in same directory


@same_content_files('Hi', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11sym'), ('f11', 'df/f11sym')])
def test_rename_symlinked_once(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/f11').absolute()), 'df/z', capsys)
    assert ck.check_rename(dry=True)
    assert ck.check_rename(dry=False)
    assert os.readlink('df/f11sym') == "z"


@same_content_files('Hi', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11sym'), ('f11', 'df/f11sym')])
def test_move_symlinked_once(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/f11').absolute()), 'ki/z', capsys)
    assert ck.check_move(dry=True)
    assert ck.check_move(dry=False)
    assert os.readlink('df/f11sym') == f"{duplicates_dir}/ki/z"


@same_content_files('Hi', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11sym'), ('f11', 'df/f11sym')])
def test_delete_symlinked_once_with_corresponding(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/f11').absolute()), 'ki/f11', capsys)
    assert ck.check_delete(dry=True)
    assert ck.check_delete(dry=False)
    assert os.readlink('df/f11sym') == f"{duplicates_dir}/ki/f11"
    assert count_files({'df': 1})


@same_content_files('Hi', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11sym'), ('f11', 'df/f11sym')])
def test_delete_symlinked_once_without_corresponding(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[], debug=True)
    ck = FP(fh, str(Path('df/f11').absolute()), None, capsys)
    assert ck.check_delete(dry=True)
    assert ck.check_delete(dry=False)
    assert count_files({'df': 0})


# Operations on files symlinked to multiple times directly in same directory


@same_content_files('Hi', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11sym'), ('f11', 'df/f11sym'), ('f11', 'df/f11sym2')])
def test_rename_symlinked_mutiple_direct(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/f11').absolute()), 'df/z', capsys)
    assert ck.check_rename(dry=True)
    assert ck.check_rename(dry=False)
    assert os.readlink('df/f11sym') == "z"
    assert os.readlink('df/f11sym2') == "z"


@same_content_files('Hi', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11sym'), ('f11', 'df/f11sym'), ('f11', 'df/f11sym2')])
def test_move_symlinked_mutiple_direct(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/f11').absolute()), 'ki/z', capsys)
    assert ck.check_move(dry=True)
    assert ck.check_move(dry=False)
    assert os.readlink('df/f11sym') == f"{duplicates_dir}/ki/z"
    assert os.readlink('df/f11sym2') == f"{duplicates_dir}/ki/z"


@same_content_files('Hi', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11sym'), ('f11', 'df/f11sym'), ('f11', 'df/f11sym2')])
def test_delete_symlinked_mutiple_direct_with_corresponding(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/f11').absolute()), 'ki/f11', capsys)
    assert ck.check_delete(dry=True)
    assert ck.check_delete(dry=False)
    assert os.readlink('df/f11sym') == f"{duplicates_dir}/ki/f11"
    assert os.readlink('df/f11sym2') == f"{duplicates_dir}/ki/f11"
    assert count_files({'df': 2})


@same_content_files('Hi', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11sym'), ('f11', 'df/f11sym'), ('f11', 'df/f11sym2')])
def test_delete_symlinked_mutiple_direct_without_corresponding(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[], debug=True)
    ck = FP(fh, str(Path('df/f11').absolute()), None, capsys)
    assert ck.check_delete(dry=True)
    assert ck.check_delete(dry=False)
    assert count_files({'df': 0})


# Operations on files symlinked to multiple times indirectly through different directories


@same_content_files('Hi', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11sym'), ('f11', 'df/f11sym'), ('f11sym', 'df/f11sym2'), ('../df/f11sym', 'ki/f11sym3')])
def test_rename_symlinked_mutiple_indirect(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/f11').absolute()), 'df/z', capsys)
    assert ck.check_rename(dry=True)
    assert ck.check_rename(dry=False)
    assert os.readlink('df/f11sym') == "z"
    assert os.readlink('df/f11sym2') == "f11sym"
    assert os.readlink('ki/f11sym3') == "../df/f11sym"


@same_content_files('Hi', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11sym'), ('f11', 'df/f11sym'), ('f11sym', 'df/f11sym2'), ('../df/f11sym', 'ki/f11sym3')])
def test_move_symlinked_mutiple_indirect(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/f11').absolute()), 'ki/z', capsys)
    assert ck.check_move(dry=True)
    assert ck.check_move(dry=False)
    assert os.readlink('df/f11sym') == f"{duplicates_dir}/ki/z"
    assert os.readlink('df/f11sym2') == "f11sym"
    assert os.readlink('ki/f11sym3') == "../df/f11sym"


@same_content_files('Hi', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11sym'), ('f11', 'df/f11sym'), ('f11sym', 'df/f11sym2'), ('../df/f11sym', 'ki/f11sym3')])
def test_delete_symlinked_mutiple_indirect_with_corresponding(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/f11').absolute()), 'ki/f11', capsys)
    assert ck.check_delete(dry=True)
    assert ck.check_delete(dry=False)
    assert os.readlink('df/f11sym') == f"{duplicates_dir}/ki/f11"
    assert os.readlink('df/f11sym2') == "f11sym"
    assert os.readlink('ki/f11sym3') == "../df/f11sym"
    assert count_files({'df': 2})


@same_content_files('Hi', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11sym'), ('f11', 'df/f11sym'), ('f11sym', 'df/f11sym2'), ('../df/f11sym', 'ki/f11sym3')])
def test_delete_symlinked_mutiple_indirect_without_corresponding(duplicates_dir, capsys):
    # TODO should we delete, leave the file or fail when deleting it will leave broken links in protect dir?
    # Option to also delete link from protect dir?
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[], debug=True)
    ck = FP(fh, str(Path('df/f11').absolute()), None, capsys)
    assert ck.check_delete(dry=True)
    assert ck.check_delete(dry=False)
    assert os.readlink('ki/f11sym3') == "../df/f11sym"
    assert not os.path.exists('ki/f11sym3')  # The link is there but broken
    assert count_files({'df': 0})
    pytest.xfail('TODO: broken symlink left in protect dir')


# Operations on files symlinked to multiple times indirectly through different directories - first symlink in protect dir pointing to file in work_on dir


@same_content_files('Hi', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11kisym'), ('../df/f11', 'ki/f11sym'), ('../ki/f11sym', 'df/f11sym2'), ('../df/f11sym2', 'ki/f11sym3')])
def test_rename_symlinked_mutiple_indirect_first_in_ki(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/f11').absolute()), 'df/z', capsys)
    assert ck.check_rename(dry=True)
    assert ck.check_rename(dry=False)
    assert os.readlink('ki/f11sym') == f"{duplicates_dir}/df/z"
    assert os.readlink('df/f11sym2') == "../ki/f11sym"
    assert os.readlink('ki/f11sym3') == "../df/f11sym2"


@same_content_files('Hi', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11kisym'), ('../df/f11', 'ki/f11sym'), ('../ki/f11sym', 'df/f11sym2'), ('../df/f11sym2', 'ki/f11sym3')])
def test_move_symlinked_mutiple_indirect_first_in_ki(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/f11').absolute()), 'ki/z', capsys)
    assert ck.check_move(dry=True)
    assert ck.check_move(dry=False)
    assert os.readlink('ki/f11sym') == "z"
    assert os.readlink('df/f11sym2') == "../ki/f11sym"
    assert os.readlink('ki/f11sym3') == "../df/f11sym2"


@same_content_files('Hi', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11kisym'), ('../df/f11', 'ki/f11sym'), ('../ki/f11sym', 'df/f11sym2'), ('../df/f11sym2', 'ki/f11sym3')])
def test_delete_symlinked_mutiple_indirect_first_in_ki_with_corresponding(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/f11').absolute()), 'ki/f11', capsys)
    assert ck.check_delete(dry=True)
    assert ck.check_delete(dry=False)
    assert os.readlink('ki/f11sym') == "f11"
    assert os.readlink('df/f11sym2') == "../ki/f11sym"
    assert os.readlink('ki/f11sym3') == "../df/f11sym2"
    assert count_files({'df': 1})


@same_content_files('Hi', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11kisym'), ('../df/f11', 'ki/f11sym'), ('../ki/f11sym', 'df/f11sym2'), ('../df/f11sym2', 'ki/f11sym3')])
def test_delete_symlinked_mutiple_indirect_first_in_ki_without_corresponding(duplicates_dir, capsys):
    # TODO should we delete, leave the file or fail when deleting it will leave broken links in protect dir?
    # Option to also delete link from protect dir?
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[], debug=True)
    ck = FP(fh, str(Path('df/f11').absolute()), None, capsys)
    assert ck.check_delete(dry=True)
    assert ck.check_delete(dry=False)
    assert os.readlink('ki/f11sym3') == "../df/f11sym2"
    assert not os.path.exists('df/f11sym2')  # The link is there but broken
    assert not os.path.exists('ki/f11sym3')  # The link is there but broken
    assert count_files({'df': 1})
    pytest.xfail('TODO: broken symlink left in protect dir')


@same_content_files('Hi', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11kisym'), ('../df/f11', 'ki/f11sym'), ('f11sym', 'ki/f11sym2')])
def test_delete_symlinked_mutiple_indirect_first_protect_without_corresponding(duplicates_dir, capsys):
    # TODO should we delete, leave the file or fail when deleting it will leave broken links in protect dir?
    # Option to also delete link from protect dir?
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[], debug=True)
    ck = FP(fh, str(Path('df/f11').absolute()), None, capsys)
    assert ck.check_delete(dry=True)
    assert ck.check_delete(dry=False)
    assert not os.path.exists('ki/f11sym2')  # The link is there but broken
    assert count_files({'df': 0})
    assert count_files({'ki': 4})
    pytest.xfail('TODO: broken symlink left in protect dir')



# Operations on files symlinked to multiple times indirectly through different directories - first symlink in protect dir pointing to outside of collected files


@same_content_files('Hi', 'outside/a.txt', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11kisym'), ('../df/f11', 'ki/f11sym'), ('../ki/f11sym', 'df/f11sym2'), ('../outside/a.txt', 'ki/f11sym3')])
def test_rename_symlinked_mutiple_indirect_first_in_ki_one_pointing_outside(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/f11').absolute()), 'df/z', capsys)
    assert ck.check_rename(dry=True)
    assert ck.check_rename(dry=False)
    assert os.readlink('ki/f11sym') == f"{duplicates_dir}/df/z"
    assert os.readlink('df/f11sym2') == "../ki/f11sym"
    assert os.readlink('ki/f11sym3') == "../outside/a.txt"


@same_content_files('Hi', 'outside/a.txt', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11kisym'), ('../df/f11', 'ki/f11sym'), ('../ki/f11sym', 'df/f11sym2'), ('../outside/a.txt', 'ki/f11sym3')])
def test_move_symlinked_mutiple_indirect_first_in_ki_one_pointing_outside(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/f11').absolute()), 'ki/z', capsys)
    assert ck.check_move(dry=True)
    assert ck.check_move(dry=False)
    assert os.readlink('ki/f11sym') == "z"
    assert os.readlink('df/f11sym2') == "../ki/f11sym"
    assert os.readlink('ki/f11sym3') == "../outside/a.txt"


@same_content_files('Hi', 'outside/a.txt', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11kisym'), ('../df/f11', 'ki/f11sym'), ('../ki/f11sym', 'df/f11sym2'), ('../outside/a.txt', 'ki/f11sym3')])
def test_delete_symlinked_mutiple_indirect_first_in_ki_one_pointing_outside_with_corresponding(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/f11').absolute()), 'ki/f11', capsys)
    assert ck.check_delete(dry=True)
    assert ck.check_delete(dry=False)
    assert os.readlink('ki/f11sym') == "f11"
    assert os.readlink('df/f11sym2') == "../ki/f11sym"
    assert os.readlink('ki/f11sym3') == "../outside/a.txt"
    assert count_files({'df': 1})


@same_content_files('Hi', 'outside/a.txt', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11kisym'), ('../df/f11', 'ki/f11sym'), ('../ki/f11sym', 'df/f11sym2'), ('../outside/a.txt', 'ki/f11sym3')])
def test_delete_symlinked_mutiple_indirect_first_in_ki_one_pointing_outside_without_corresponding(duplicates_dir, capsys):
    # TODO should we delete, leave the file or fail when deleting it will leave broken links in protect dir?
    # Option to also delete link from protect dir?
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[], debug=True)
    ck = FP(fh, str(Path('df/f11').absolute()), None, capsys)
    assert ck.check_delete(dry=True)
    assert ck.check_delete(dry=False)
    assert os.readlink('ki/f11sym3') == "../outside/a.txt"
    assert not os.path.exists('df/f11sym2')  # The link is there but broken
    assert os.path.exists('ki/f11sym3')
    assert count_files({'df': 1})
    pytest.xfail('TODO: broken symlink left in protect dir')


# Delete symlinks option


@same_content_files('Hi', 'outside/a.txt', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11kisym'), ('../df/f11', 'ki/f11sym'), ('../ki/f11sym', 'df/f11sym2'), ('../outside/a.txt', 'ki/f11sym3'), ('f11', 'df/f11sym')])
def test_rename_symlinked_mutiple_indirect_first_in_ki_one_pointing_outside_delete_symlinks(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[], delete_symlinks_instead_of_relinking=True)
    ck = FP(fh, str(Path('df/f11').absolute()), 'df/z', capsys)
    assert ck.check_rename(dry=True)
    assert ck.check_rename(dry=False)
    assert os.readlink('ki/f11sym') == f"{duplicates_dir}/df/z"
    assert os.readlink('df/f11sym2') == "../ki/f11sym"
    assert os.readlink('ki/f11sym3') == "../outside/a.txt"
    assert not os.path.exists('df/f11sym')
    assert count_files({'df': 2})


# Explicitly deleting symlinks


@same_content_files('Hi', 'outside/a.txt', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11kisym'), ('../df/f11', 'ki/f11sym'), ('../ki/f11sym', 'df/f11sym2'), ('../outside/a.txt', 'ki/f11sym3'), ('f11', 'df/f11sym')])
def test_replace_a_symlink_with_the_file_it_points_to(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[], delete_symlinks_instead_of_relinking=True)
    abs_f11_sym = str(Path('df/f11sym').absolute())
    abs_f11 = str(Path('df/f11').absolute())

    print('-------------------------- dry_run -------------------------------')
    assert fh.registered_delete(abs_f11_sym, 'f11')
    assert fh.registered_rename(abs_f11, 'df/f11sym')
    assert count_files({'df': 3})

    fh.dry_run = False
    fh.reset()
    print('-------------------------- do_it -------------------------------')
    assert fh.registered_delete(abs_f11_sym, 'f11')
    assert fh.registered_rename(abs_f11, 'df/f11sym')

    assert os.path.exists('df/f11sym')
    assert not os.path.islink('df/f11sym')
    assert not os.path.exists('df/f11')

    assert os.readlink('df/f11sym2') == "../ki/f11sym"
    assert os.readlink('ki/f11sym3') == "../outside/a.txt"
    assert count_files({'df': 2})


# Stats


@same_content_files('Hi', 'ki/f11', 'df/f11')
@symlink_files([('f11', 'ki/f11kisym'), ('../df/f11', 'ki/f11sym'), ('../ki/f11sym', 'df/f11sym2'), ('../df/f11sym2', 'ki/f11sym3')])
def test_stats(duplicates_dir, capsys):
    fh = FileHandler(['ki'], ['df'], None, dry_run=True, protected_regexes=[])
    ck = FP(fh, str(Path('df/f11').absolute()), 'df/z', capsys)

    assert ck.check_rename(dry=True)
    with fh.stats():
        print('did nothing')

    out, _ = capsys.readouterr()
    assert 'DRY' in out

    assert ck.check_rename(dry=False)
    with fh.stats():
        print('did stuff')

    out, _ = capsys.readouterr()
    assert 'DRY' not in out

    pytest.xfail('TODO: validate stats output')
