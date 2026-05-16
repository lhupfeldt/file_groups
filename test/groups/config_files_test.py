import re
import pprint

from file_groups.groups import FileGroups
from file_groups.config.config_handler import ConfigHandler

from ..conftest import same_content_files, dir_conf_files
from ..config.config_files_test import set_conf_dirs
from .utils import FGC


@same_content_files('B', 'ki/df/KEEP_ME.JPEG')
@dir_conf_files([], [r'KEEP_ME\..*'], 'ki/.file_groups.conf')
def test_file_groups_group_files_by_config_protect_simple(duplicates_dir, set_conf_dirs, log_debug):
    """'ki/df/KEEP_ME.jpg' should be protected."""

    with FGC(FileGroups(['ki'], ['ki/df']), duplicates_dir) as ck:
        assert ck.ckfl(
            'must_protect.files',
            'ki/df/KEEP_ME.JPEG')


@same_content_files("Hejsa", 'ki/Af11.jpg', 'df/Bf11.jpg')
@dir_conf_files([r'xxx.*xxx', r'yyy.*yyy'], [r'zzz'], 'ki/file_groups.conf')
@dir_conf_files([r'a.*\.b'], [r'zzz2.*'], 'df/.file_groups.conf')
def test_file_groups_sys_user_config_files_no_global(duplicates_dir, set_conf_dirs):
    with FGC(FileGroups(['ki'], ['df'], config_handler=ConfigHandler()), duplicates_dir) as ck:
        print("ck.fg.dirs:", ck.fg.dirs)
        assert ck.ckfl('must_protect.files', 'ki/Af11.jpg')
        assert ck.ckfl('may_work_on.files', 'df/Bf11.jpg')

    pprint.pprint(ck.fg.config_handler.global_config)
    assert ck.fg.config_handler.global_config.protect_recursive == set()

    assert ck.fg.dirs[str(duplicates_dir/"ki")].dir_config.protect_local == set([re.compile(r"xxx.*xxx"), re.compile(r"yyy.*yyy")])
    assert ck.fg.dirs[str(duplicates_dir/"ki")].dir_config.protect_recursive == set([re.compile(r"zzz")])

    assert ck.fg.dirs[str(duplicates_dir/"df")].dir_config.protect_local == set([re.compile(r"a.*\.b")])
    assert ck.fg.dirs[str(duplicates_dir/"df")].dir_config.protect_recursive == set([re.compile(r"zzz2.*")])

    ck.fg.stats()
