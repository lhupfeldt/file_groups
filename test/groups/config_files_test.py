import re
import pprint

from file_groups.groups import FileGroups
from file_groups.config_files import ConfigFiles

from ..conftest import same_content_files, dir_conf_files
from ..config_files_test import set_conf_dirs
from .utils import FGC


@same_content_files("Hejsa", 'ki/Af11.jpg', 'df/Bf11.jpg')
@dir_conf_files([r'xxx.*xxx', r'yyy.*yyy'], [r'zzz'], 'ki/file_groups.conf')
@dir_conf_files([r'a.*\.b'], [r'zzz2.*'], 'df/.file_groups.conf')
def test_file_groups_sys_user_config_files_no_global(duplicates_dir, set_conf_dirs):
    with FGC(FileGroups(['ki'], ['df'], config_files=ConfigFiles(remember_configs=True)), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'ki/Af11.jpg')
        assert ck.ckfl('may_work_on.files', 'df/Bf11.jpg')

    pprint.pprint(ck.fg.config_files._global_config)  # pylint: disable=protected-access
    assert ck.fg.config_files._global_config.protect_recursive == set()  # pylint: disable=protected-access

    pprint.pprint(ck.fg.config_files.per_dir_configs)

    assert list(ck.fg.config_files.per_dir_configs.keys()) == [duplicates_dir/"ki", duplicates_dir/"df"]

    assert ck.fg.config_files.per_dir_configs[duplicates_dir/"ki"].protect_local == set([re.compile(r"xxx.*xxx"), re.compile(r"yyy.*yyy")])
    assert ck.fg.config_files.per_dir_configs[duplicates_dir/"ki"].protect_recursive == set([re.compile(r"zzz")])

    assert ck.fg.config_files.per_dir_configs[duplicates_dir/"df"].protect_local == set([re.compile(r"a.*\.b")])
    assert ck.fg.config_files.per_dir_configs[duplicates_dir/"df"].protect_recursive == set([re.compile(r"zzz2.*")])

    ck.fg.stats()
