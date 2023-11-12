import re

import pytest

from file_groups.groups import FileGroups

from ..conftest import same_content_files, different_content_files, symlink_files, hardlink_files
from .utils import FGC, ckfl


@same_content_files("Hi", 'df/f11', 'ki/f12')
@same_content_files("Hello", 'df/f21', 'ki/f22')
@different_content_files("obase", 'df/f31', 'ki/f32')
def test_file_groups_unrelated_dirs(duplicates_dir):
    """Unrelated work_on and protect dirs"""
    with FGC(FileGroups(["ki"], ["df"]), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'ki/f12', 'ki/f22', 'ki/f32')
        assert ck.ckfl('may_work_on.files', 'df/f11', 'df/f21', 'df/f31')


@same_content_files("Hi", 'df/f11', 'df/ki/f12')
@same_content_files("Hello", 'df/f21', 'df/ki/f22')
@different_content_files("base", 'df/f31', 'df/ki/f32')
def test_file_groups_protect_dir_under_work_on_dir(duplicates_dir):
    """Specified protect dir underneath work_on dir"""
    with FGC(FileGroups(["df/ki"], ["df"]), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'df/ki/f12', 'df/ki/f22', 'df/ki/f32')
        assert ck.ckfl('may_work_on.files', 'df/f11', 'df/f21', 'df/f31')


@same_content_files("Hi", 'ki/df/f11', 'ki/f12')
@same_content_files("Hello", 'ki/df/f21', 'ki/f22')
@different_content_files("base", 'ki/df/f31', 'ki/f32')
def test_file_groups_work_on_dir_under_protect_dir(duplicates_dir):
    """Specified work_on dir underneath protect dir"""
    with FGC(FileGroups(["ki"], ["ki/df"]), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'ki/f12', 'ki/f22', 'ki/f32')
        assert ck.ckfl('may_work_on.files', 'ki/df/f11', 'ki/df/f21', 'ki/df/f31')


@same_content_files("Hi", 'ki/df/f11', 'ki/f11')
@same_content_files("Hello", 'ki/df/f21', 'ki/f21')
@different_content_files("base", 'ki/df/f31', 'ki/f31')
def test_file_groups_names_are_irelevant(duplicates_dir):
    """Just a weird test with a different filename - specified work_on dir underneath protect dir"""
    with FGC(FileGroups(["ki"], ["ki/df"]), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'ki/f11', 'ki/f21', 'ki/f31')
        assert ck.ckfl('may_work_on.files', 'ki/df/f11', 'ki/df/f21', 'ki/df/f31')


@same_content_files("Hi", 'ki/df/f11', 'ki/df/df/f21', 'ki/df/df2/f21', 'ki/f12')
def test_file_groups_work_on_dir_subdirs(duplicates_dir):
    """work_on dir with subdirs underneath protect dir"""
    with FGC(FileGroups(["ki"], ["ki/df"]), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'ki/f12')
        assert ck.ckfl('may_work_on.files', 'ki/df/df/f21', 'ki/df/df2/f21', 'ki/df/f11')


@same_content_files("Hejsa", 'ki1/df/f11', 'ki1/f11', 'ki2/f11')
@same_content_files("Hejsa", 'ki1/df/f12', 'ki1/f12', 'ki2/f12')
@same_content_files("Hello", 'ki1/df/f21', 'ki1/f21', 'ki2/f21')
@same_content_files("Hello", 'ki1/df/f22', 'ki1/f22', 'ki2/f22')
@same_content_files("More cow bells", 'ki1/df/f31', 'ki2/f32')
@different_content_files("base", 'ki1/df/f41', 'ki1/f41', 'ki2/f41')
def test_file_groups_two_protect_dirs(duplicates_dir):
    """Multiple protect dirs"""
    with FGC(FileGroups(["ki1", "ki2"], ["ki1/df"]), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'ki1/f11', 'ki1/f12', 'ki1/f21', 'ki1/f22', 'ki1/f41', 'ki2/f11', 'ki2/f12', 'ki2/f21', 'ki2/f22', 'ki2/f32', 'ki2/f41')
        assert ck.ckfl('may_work_on.files', 'ki1/df/f11', 'ki1/df/f12', 'ki1/df/f21', 'ki1/df/f22', 'ki1/df/f31', 'ki1/df/f41')


@same_content_files("Hejsa", 'ki1/df/f11', 'ki1/f11', 'df2/f11')
@same_content_files("Hejsa", 'ki1/df/f12', 'ki1/f12', 'df2/f12')
@same_content_files("Hello", 'ki1/df/f21', 'ki1/f21', 'df2/f21')
@same_content_files("Hello", 'ki1/df/f22', 'ki1/f22', 'df2/f22')
@same_content_files("More cow bells", 'ki1/df/f31', 'df2/f32')
@different_content_files("base", 'ki1/df/f41', 'ki1/f41', 'df2/f41')
def test_file_groups_two_work_on_dirs(duplicates_dir):
    """Multiple work_on dirs"""
    with FGC(FileGroups(["ki1"], ["df2", "ki1/df"]), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'ki1/f11', 'ki1/f12', 'ki1/f21', 'ki1/f22', 'ki1/f41')
        assert ck.ckfl(
            'may_work_on.files',
            'df2/f11', 'df2/f12', 'df2/f21', 'df2/f22', 'df2/f32', 'df2/f41', 'ki1/df/f11', 'ki1/df/f12', 'ki1/df/f21', 'ki1/df/f22', 'ki1/df/f31', 'ki1/df/f41')


@same_content_files("Hejsa", 'ki1/df/f11', 'ki1/df/ki12/f11', 'ki1/df/ki13/f11', 'ki1/df/ki13/ki14/f11', 'ki1/df/ki13/df12/f11', 'ki1/f11', 'df2/f11')
@same_content_files("Hejsa", 'ki1/df/f12', 'ki1/df/ki12/f12', 'ki1/df/ki13/f12', 'ki1/df/ki13/ki14/f12', 'ki1/df/ki13/df12/f12', 'ki1/f12', 'df2/f12')
@same_content_files("Hello", 'ki1/df/f21', 'ki1/df/ki12/f21', 'ki1/df/ki13/f21', 'ki1/df/ki13/ki14/f21', 'ki1/df/ki13/df12/f21', 'ki1/f21', 'df2/f21')
@same_content_files("Hello", 'ki1/df/f22', 'ki1/df/ki12/f22', 'ki1/df/ki13/f22', 'ki1/df/ki13/ki14/f22', 'ki1/df/ki13/df12/f22', 'ki1/f22', 'df2/f22')
@same_content_files("More cow bells", 'ki1/df/f31', 'df2/f32')
@different_content_files("base", 'ki1/df/f41', 'ki1/df/ki12/f41', 'ki1/df/ki13/ki14/fffff4.txt', 'ki1/f41', 'df2/f41')
@different_content_files("base", 'ki1/df/f51', 'ki1/df/ki12/f51', 'ki1/df/ki13/ki14/fffff5.txt', 'ki1/f51', 'df2/f51')
def test_file_groups_multiple_levels_nested_work_on_and_protect_dirs(duplicates_dir):
    """Multiple protect dirs

    Protect:
    ki1 -> 6
    ki1/df -> 3
    ki1/df/ki12 -> 4
    ki1/df/ki13 -> 4
    ki1/df/ki13/ki14 -> 4
    df2 -> 3
    total: 24

    Work On:
    ki1/df -> 4
    ki1/df/ki13/df12 -> 4
    df2 -> 4
    total: 12
    """

    kargs = ["ki1", "ki1/df/ki12", "ki1/df/ki13", "ki1/df/ki13/ki14"]
    dargs = ["df2", "ki1/df", "ki1/df/ki13/df12"]

    with FGC(FileGroups(kargs, dargs), duplicates_dir) as ck:
        assert ck.ckfl(
            'must_protect.files',
            'ki1/df/ki12/f11', 'ki1/df/ki12/f12', 'ki1/df/ki12/f21', 'ki1/df/ki12/f22', 'ki1/df/ki12/f41', 'ki1/df/ki12/f51',
            'ki1/df/ki13/f11', 'ki1/df/ki13/f12', 'ki1/df/ki13/f21', 'ki1/df/ki13/f22',
            'ki1/df/ki13/ki14/f11', 'ki1/df/ki13/ki14/f12', 'ki1/df/ki13/ki14/f21', 'ki1/df/ki13/ki14/f22', 'ki1/df/ki13/ki14/fffff4.txt', 'ki1/df/ki13/ki14/fffff5.txt',
            'ki1/f11', 'ki1/f12', 'ki1/f21', 'ki1/f22', 'ki1/f41', 'ki1/f51')
        assert ck.ckfl(
            'may_work_on.files',
            'df2/f11', 'df2/f12', 'df2/f21', 'df2/f22', 'df2/f32', 'df2/f41', 'df2/f51',
            'ki1/df/f11', 'ki1/df/f12', 'ki1/df/f21', 'ki1/df/f22', 'ki1/df/f31', 'ki1/df/f41', 'ki1/df/f51',
            'ki1/df/ki13/df12/f11', 'ki1/df/ki13/df12/f12', 'ki1/df/ki13/df12/f21', 'ki1/df/ki13/df12/f22')


@same_content_files("Hi", 'df/f11', 'ki/f12')
@same_content_files("Hello", 'df/f21', 'ki/f22')
@different_content_files("base", 'df/f31', 'ki/f32')
@symlink_files([('f12', 'ki/f12sym'), ('f11', 'df/f11sym')])
def test_file_groups_unrelated_dirs_symlinks(duplicates_dir):
    """Unrelated work_on and protect dirs both with symlinks"""
    with FGC(FileGroups(["ki"], ["df"]), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'ki/f12', 'ki/f22', 'ki/f32')
        assert ck.ckfl('must_protect.symlinks', 'ki/f12sym')
        assert ck.cksfl('must_protect.symlinks_by_abs_points_to', {'ki/f12': ['ki/f12sym']})
        assert ck.ckfl('may_work_on.files', 'df/f11', 'df/f21', 'df/f31')
        assert ck.ckfl('may_work_on.symlinks', 'df/f11sym')
        assert ck.cksfl('may_work_on.symlinks_by_abs_points_to', {'df/f11': ['df/f11sym']})


@same_content_files("Hi", 'df/f11', 'ki/f12')
@symlink_files([('f11', 'df/f11sym1')])
@symlink_files([('f11sym1', 'df/f11sym2')])
@symlink_files([('f11sym2', 'df/f11sym3')])
def test_file_groups_multi_level_symlinked_symlinks(duplicates_dir):
    """Unrelated work_on and protect dirs both with symlinks to symlinks"""
    with FGC(FileGroups(["ki"], ["df"]), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'ki/f12')
        assert ck.ckfl('may_work_on.files', 'df/f11')
        assert ck.ckfl('may_work_on.symlinks', 'df/f11sym1', 'df/f11sym2', 'df/f11sym3')
        assert ck.cksfl('may_work_on.symlinks_by_abs_points_to', {'df/f11': ['df/f11sym1'], 'df/f11sym1': ['df/f11sym2'], 'df/f11sym2': ['df/f11sym3']})


@same_content_files("Hi", 'df/f11', 'ki/f12')
@same_content_files("Hello", 'df/f21', 'ki/f22')
@different_content_files("base", 'df/f31', 'ki/f32')
@symlink_files([('nowhere/f12', 'ki/f12sym'), ('nowhere', 'df/f12sym')], broken=True)
def test_file_groups_unrelated_dirs_broken_symlinks(duplicates_dir):
    """Unrelated work_on and protect dirs both with symlinks"""
    with FGC(FileGroups(["ki"], ["df"]), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'ki/f12', 'ki/f22', 'ki/f32')
        assert ck.ckfl('must_protect.symlinks', 'ki/f12sym')
        assert ck.cksfl('must_protect.symlinks_by_abs_points_to', {'ki/nowhere/f12': ['ki/f12sym']})
        assert ck.ckfl('may_work_on.files', 'df/f11', 'df/f21', 'df/f31')
        assert ck.ckfl('may_work_on.symlinks', 'df/f12sym')
        assert ck.cksfl('may_work_on.symlinks_by_abs_points_to', {'df/nowhere': ['df/f12sym']})


@same_content_files("Hi", 'df/f11', 'ki/f12')
@same_content_files("Hello", 'df/f21', 'ki/f22')
@symlink_files([('f12', 'ki/f12sym'), ('f11', 'df/f11sym'), ('f11', 'df/f11sym2')])
@different_content_files("base", 'df/f31', 'ki/f32')
@symlink_files([('f31', 'df/f31sym'),])
def test_file_groups_unrelated_dirs_multiple_symlinks_in_df_to_same_file_in_ki(duplicates_dir):
    """Unrelated work_on and protect dirs both with symlinks"""
    with FGC(FileGroups(["ki"], ["df"]), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'ki/f12', 'ki/f22', 'ki/f32')
        assert ck.ckfl('must_protect.symlinks', 'ki/f12sym')
        assert ck.cksfl('must_protect.symlinks_by_abs_points_to', {'ki/f12': ['ki/f12sym']})
        assert ck.ckfl('may_work_on.files', 'df/f11', 'df/f21', 'df/f31')
        assert ck.ckfl('may_work_on.symlinks', 'df/f11sym', 'df/f11sym2', 'df/f31sym')
        assert ck.cksfl('may_work_on.symlinks_by_abs_points_to', {'df/f11': ['df/f11sym', 'df/f11sym2'], 'df/f31': ['df/f31sym']})


@same_content_files("Hi", 'df/f11', 'ki/f12')
@same_content_files("Hello", 'df/f21', 'ki/f22')
@symlink_files([('f12', 'ki/f12sym'), ('f12', 'ki/f12sym2'), ('f11', 'df/f11sym')])
@different_content_files("base", 'df/f31', 'ki/f32')
@symlink_files([('f31', 'df/f31sym'),])
def test_file_groups_unrelated_dirs_multiple_symlinks_in_ki_to_same_file_in_df(duplicates_dir):
    """Unrelated work_on and protect dirs both with symlinks"""
    with FGC(FileGroups(["ki"], ["df"]), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'ki/f12', 'ki/f22', 'ki/f32')
        assert ck.ckfl('must_protect.symlinks', 'ki/f12sym', 'ki/f12sym2')
        assert ck.cksfl('must_protect.symlinks_by_abs_points_to', {'ki/f12': ['ki/f12sym', 'ki/f12sym2']})
        assert ck.ckfl('may_work_on.files', 'df/f11', 'df/f21', 'df/f31')
        assert ck.ckfl('may_work_on.symlinks', 'df/f11sym', 'df/f31sym')
        assert ck.cksfl('may_work_on.symlinks_by_abs_points_to', {'df/f11': ['df/f11sym'], 'df/f31': ['df/f31sym']})


@same_content_files("Hi", 'df/f11', 'ki/f12')
@same_content_files("Hello", 'df/f21', 'ki/f22')
@different_content_files("base", 'df/f31', 'ki/f32')
@symlink_files([('../df/f11', 'ki/f11sym')])
def test_file_groups_symlinks_from_protect_to_work_on_dirs_symlinks(duplicates_dir):
    """Unrelated work_on and protect dirs symlink from protect dir to work_on dir"""
    with FGC(FileGroups(["ki"], ["df"]), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'ki/f12', 'ki/f22', 'ki/f32')
        assert ck.ckfl('must_protect.symlinks', 'ki/f11sym')
        assert ck.cksfl('must_protect.symlinks_by_abs_points_to', {'df/f11': ['ki/f11sym']})
        assert ck.ckfl('may_work_on.files', 'df/f11', 'df/f21', 'df/f31')


@same_content_files("Hi", 'df/f11', 'ki/f12')
@same_content_files("Hello", 'df/f21', 'ki/f22')
@different_content_files("base", 'df/f31', 'ki/f32')
@same_content_files('Whatever', 'df/f41')
@hardlink_files([('df/f41', 'df/f41hard')])
def test_file_groups_unrelated_dirs_hardlinks_within_work_on(duplicates_dir):
    """Unrelated work_on and protect dirs - hardlink to otherwise not duplicated file in work_on-from-dir"""
    with FGC(FileGroups(["ki"], ["df"]), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'ki/f12', 'ki/f22', 'ki/f32')
        assert ck.ckfl('may_work_on.files', 'df/f11', 'df/f21', 'df/f31', 'df/f41', 'df/f41hard')


@same_content_files("Hejsa", 'ki1/df/f11', 'ki1/df/ki12/f11', 'ki1/df/ki13/f11', 'ki1/df/ki13/ki14/f11', 'ki1/df/ki13/df12/f11', 'ki1/f11', 'df2/f11')
@same_content_files("Hejsa", 'ki1/df/f12', 'ki1/df/ki12/f12', 'ki1/df/ki13/f12', 'ki1/df/ki13/ki14/f12', 'ki1/df/ki13/df12/f12', 'ki1/f12', 'df2/f12')
@same_content_files("Hello", 'ki1/df/f21', 'ki1/df/ki12/f21', 'ki1/df/ki13/f21', 'ki1/df/ki13/ki14/f21', 'ki1/df/ki13/df12/f21', 'ki1/f21', 'df2/f21')
@same_content_files("Hello", 'ki1/df/f22', 'ki1/df/ki12/f22', 'ki1/df/ki13/f22', 'ki1/df/ki13/ki14/f22', 'ki1/df/ki13/df12/f22', 'ki1/f22', 'df2/f22')
@same_content_files("More cow bells", 'ki1/df/f31', 'df2/f32')
@different_content_files("base", 'ki1/df/f41', 'ki1/df/ki12/f41', 'ki1/df/ki13/ki14/fffff4.txt', 'ki1/f41', 'df2/f41')
@different_content_files("base", 'ki1/df/f512', 'ki1/df/ki12/f512', 'ki1/df/ki13/ki14/fffff52.txt', 'ki1/f512', 'df2/f512')
def test_file_groups_multiple_levels_nested_work_on_and_protect_dirs_with_pattern_and_debug(duplicates_dir, log_debug):
    """Multiple protect dirs

    Protect:
    ki1 -> 6
    ki1/df -> 3
    ki1/df/ki12 -> 4
    ki1/df/ki13 -> 4
    ki1/df/ki13/ki14 -> 4
    df2 -> 3
    total: 24

    Work_On:
    ki1/df -> 4
    ki1/df/ki13/df12 -> 4
    df2 -> 4
    total: 12
    """

    kargs = ["ki1", "ki1/df/ki12", "ki1/df/ki13", "ki1/df/ki13/ki14"]
    dargs = ["df2", "ki1/df", "ki1/df/ki13/df12"]

    # Exclude from protected filenames where the 'stem' ends with 4 or 1
    # Include in work_on filenames where the 'stem' ends with 1
    with FGC(FileGroups(kargs, dargs, protect_exclude=re.compile(r'.*[41](\..*)?$'), work_include=re.compile(r'.*1(\..*)?$')), duplicates_dir) as ck:
        assert ck.ckfl(
            'must_protect.files',
            'ki1/df/ki12/f12', 'ki1/df/ki12/f22',
            'ki1/df/ki12/f512', 'ki1/df/ki13/f12', 'ki1/df/ki13/f22',
            'ki1/df/ki13/ki14/f12', 'ki1/df/ki13/ki14/f22', 'ki1/df/ki13/ki14/fffff52.txt',
            'ki1/f12', 'ki1/f22', 'ki1/f512')
        assert ck.ckfl(
            'may_work_on.files',
            'df2/f11', 'df2/f21', 'df2/f41',
            'ki1/df/f11', 'ki1/df/f21', 'ki1/df/f31', 'ki1/df/f41',
            'ki1/df/ki13/df12/f11', 'ki1/df/ki13/df12/f21')

    ck.fg.stats()
    out = log_debug.text
    assert 'collected protect_directories:' in out
    assert 'collected protect_directory_symlinks:' in out
    assert 'collected work_on_directories:' in out
    assert 'collected work_on_directory_symlinks:' in out
    assert 'collected must_protect_files:' in out
    assert 'collected must_protect_symlinks:' in out
    assert 'collected may_work_on_files:' in out
    assert 'collected may_work_on_symlinks:' in out
    pytest.xfail('TODO: directory counts')


@same_content_files("Hejsa", 'ki1/df/f11.xtx', 'ki1/df/ki12/f11', 'ki1/df/ki13/f11', 'ki1/df/ki13/ki14/f11', 'ki1/df/ki13/df12/f11.txt')
@different_content_files("base", 'ki1/df/f41', 'ki1/df/ki12/f41.xtx', 'ki1/df/ki13/ki14/fffff4.txt', 'ki1/f41')
def test_file_groups_multiple_levels_nested_work_on_and_protect_dirs_with_pattern_no_debug(duplicates_dir):
    """Multiple protect dirs"""
    kargs = ["ki1", "ki1/df/ki12", "ki1/df/ki13", "ki1/df/ki13/ki14"]
    dargs = ["ki1/df", "ki1/df/ki13/df12"]

    with FGC(FileGroups(kargs, dargs, protect_exclude=re.compile(r'.*\.txt$'), work_include=re.compile(r'.*\.xtx$')), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'ki1/df/ki12/f11', 'ki1/df/ki12/f41.xtx', 'ki1/df/ki13/f11', 'ki1/df/ki13/ki14/f11', 'ki1/f41')
        assert ck.ckfl('may_work_on.files', 'ki1/df/f11.xtx')

    ck.fg.stats()


@same_content_files("Hi", 'xx/f11', 'xx/f12')
@different_content_files("base", 'xx/f31', 'xx/f32')
def test_file_groups_specified_protect_dir_same_as_work_on_dir(duplicates_dir, log_debug):
    """protect dir same as work_on dir -> work_on-dir is ignored."""
    fg = FileGroups(["xx"], ["xx"])

    assert "Ignoring 'work' dir 'xx' which is also a 'protect' dir." in log_debug.text
    assert ckfl("must_protect.files", fg.must_protect.files, 'xx/f11', 'xx/f12', 'xx/f31', 'xx/f32')


@same_content_files("Hi", 'xx/f11', 'xx/f12')
@different_content_files("base", 'xx/f31', 'xx/f32')
@different_content_files("bip", 'xx/yy/f41')
def test_file_groups_resolved_protect_dir_same_as_work_on_dir(duplicates_dir, log_debug):
    """protect dir same as work_on dir -> work_on-dir is ignored."""
    fg = FileGroups(["xx"], ["xx/yy/../../xx"])

    assert f"Ignoring 'work' dir '{duplicates_dir}/xx' (from argument 'xx/yy/../../xx') which is also a 'protect' dir (from argument 'xx')" in log_debug.text
    assert ckfl("must_protect.files", fg.must_protect.files, 'xx/f11', 'xx/f12', 'xx/f31', 'xx/f32', 'xx/yy/f41')


@same_content_files("Hi", 'ki/f11', 'df2.txt')
def test_dir_args_df_work_on_is_a_file_not_a_dir(duplicates_dir):
    """Arg is a file not a directory"""

    with pytest.raises(NotADirectoryError) as exinfo:
        FileGroups(["ki"], ["df2.txt"])

    assert f"[Errno 20] Not a directory: '{duplicates_dir}/df2.txt'" in str(exinfo.value)


@same_content_files("Hi", 'ki/f11')
def test_dir_args_df_work_on_is_not_a_dir_does_not_exist(duplicates_dir):
    """Arg is not a directory - does not exist"""

    with pytest.raises(Exception) as exinfo:
        FileGroups(["ki"], ["df"])

    assert f"[Errno 2] No such file or directory: '{duplicates_dir}/df'" in str(exinfo.value)


@same_content_files("Hi", 'ki.txt', 'df')
def test_dir_args_df_protect_is_a_file_not_a_dir(duplicates_dir):
    """Arg is a file not a directory"""

    with pytest.raises(Exception) as exinfo:
        FileGroups(["ki.txt"], ["df"])

    assert f"[Errno 20] Not a directory: '{duplicates_dir}/ki.txt'" in str(exinfo.value)


@same_content_files("Hi", 'df/a.b')
def test_dir_args_df_protect_is_not_a_dir_does_not_exist(duplicates_dir):
    """Arg is not a directory - does not exist"""

    with pytest.raises(Exception) as exinfo:
        FileGroups(["ki"], ["df"])

    assert f"[Errno 2] No such file or directory: '{duplicates_dir}/ki'" in str(exinfo.value)


@same_content_files("Hi", 'df/f11', 'ki/f12')
@same_content_files("Hello", 'df/f21', 'ki/f22')
@symlink_files([('f12', 'ki/f12sym'), ('f11', 'df/f11sym'), ('f11', 'df/f11sym2')])
@different_content_files("base", 'df/f31', 'ki/f32')
@symlink_files([('f31', 'df/f31sym'),])
def test_file_groups_dump(duplicates_dir, log_debug):
    fg = FileGroups(["ki"], ["df"])
    fg.dump()

    out = log_debug.text
    assert 'must protect:' in out
    assert 'must protect symlinks:' in out
    assert 'must protect symlinks by absolute points to:' in out
    assert 'may work on:' in out
    assert 'may work on symlinks:' in out
    assert 'may work on symlinks by absolute points to:' in out
    pytest.xfail('TODO: verify output files')


@same_content_files("Hi", 'df/f11', 'ki/f12')
def test_file_groups_no_debug_log_dump(duplicates_dir, caplog):
    fg = FileGroups(["ki"], ["df"])
    fg.dump()

    out = caplog.text
    assert 'must protect:' not in out
