import pytest

from file_groups.groups import FileGroups

from ..conftest import same_content_files, symlink_files
from .utils import FGC


@same_content_files("Hi", 'df/f11', 'ki/f12')
@same_content_files("Hello", 'df/f21', 'ki/f22')
@symlink_files([('ki', 'kisym')])
def test_file_groups_specified_symlinks_to_protect_dirs(duplicates_dir):
    """Specify a directory for a protect dir"""
    with FGC(FileGroups(["kisym"], ["df"]), duplicates_dir) as ck:
        assert ck.ckfl('may_work_on.files', 'df/f11', 'df/f21')
        pytest.xfail('TODO: option to not follow specified protect symlinks?')

        assert ck.fg.must_protect.num_directories == 0
        assert ck.fg.must_protect.num_directory_symlinks == 0
        assert ck.fg.may_work_on.num_directories == 1
        assert ck.fg.may_work_on.num_directory_symlinks == 0


@same_content_files("Hi", 'df/f11', 'ki/f12')
@same_content_files("Hello", 'df/f21', 'ki/f22')
@symlink_files([('df', 'dfsym')])
def test_file_groups_specified_symlinks_to_work_on_dirs(duplicates_dir):
    """Specify a directory for a protect dir"""
    with FGC(FileGroups(["ki"], ["dfsym"]), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'ki/f12', 'ki/f22')
        pytest.xfail('TODO: option to not follow specified work_on symlinks?')

        assert ck.fg.must_protect.num_directories == 1
        assert ck.fg.must_protect.num_directory_symlinks == 0
        assert ck.fg.may_work_on.num_directories == 0
        assert ck.fg.may_work_on.num_directory_symlinks == 0


@same_content_files("Hi", 'df/f11', 'ki/f12')
@same_content_files("Hello", 'df/f21', 'ki/f22', 'ki/ki2/f31')
@symlink_files([('ki2', 'ki/ki2sym'), ('ki2', 'ki/ki2sym2'), ('../ki/ki2', 'df/ki2sym')])
def test_file_groups_found_symlinks_to_protect_dirs(duplicates_dir):
    """Symlinks to protect dir from both protect and work_on dirs"""
    with FGC(FileGroups(["ki"], ["df"]), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'ki/f12', 'ki/f22', 'ki/ki2/f31')
        assert ck.ckfl('may_work_on.files', 'df/f11', 'df/f21')
        assert ck.fg.must_protect.num_directories == 2
        assert ck.fg.must_protect.num_directory_symlinks == 2
        assert ck.fg.may_work_on.num_directories == 1
        assert ck.fg.may_work_on.num_directory_symlinks == 1


@same_content_files("Hi", 'df/f11', 'df/df2/f31', 'ki/f12')
@same_content_files("Hello", 'df/f21', 'ki/f22')
@symlink_files([('df2', 'df/df2sym'), ('df2', 'df/df2sym2'), ('../df/df2', 'ki/df2sym')])
def test_file_groups_found_symlinks_to_work_on_dirs(duplicates_dir):
    """Symlinks to work_on dir from both protect and work_on dirs"""
    with FGC(FileGroups(["ki"], ["df"]), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'ki/f12', 'ki/f22')
        assert ck.ckfl('may_work_on.files', 'df/df2/f31', 'df/f11', 'df/f21')
        assert ck.fg.must_protect.num_directories == 1
        assert ck.fg.must_protect.num_directory_symlinks == 1
        assert ck.fg.may_work_on.num_directories == 2
        assert ck.fg.may_work_on.num_directory_symlinks == 2
