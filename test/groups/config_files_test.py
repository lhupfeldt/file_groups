import re
import pprint

from file_groups.groups import FileGroups

from ..conftest import same_content_files
from ..config_files_test import set_conf_dirs
from .utils import FGC


@same_content_files("Hejsa", 'ki/Af11.jpg', 'df/Bf11.jpg')
def test_file_groups_sys_user_config_files_no_global(duplicates_dir, set_conf_dirs):
    with FGC(FileGroups(['ki'], ['df'], remember_configs=True), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'ki/Af11.jpg')
        assert ck.ckfl('may_work_on.files', 'df/Bf11.jpg')

    pprint.pprint(ck.fg.config_files._global_config)
    assert ck.fg.config_files._global_config.protect == {
        'local': set(),
        'recursive': set()
    }

    site_config_dir, user_config_dir = set_conf_dirs
    pprint.pprint(ck.fg.config_files.per_dir_configs)

    assert list(ck.fg.config_files.per_dir_configs.keys()) == [
        str(site_config_dir),
        str(user_config_dir),
        f"{duplicates_dir}/ki",
        f"{duplicates_dir}/df",
    ]

    assert ck.fg.config_files.per_dir_configs[str(site_config_dir)].protect == {
        "local": set([re.compile(r"P1.*\.jpg"), re.compile(r"P2.*\.jpg")]),
        "recursive": set([re.compile(r"PR1.*\.jpg")]),
    }

    assert ck.fg.config_files.per_dir_configs[str(user_config_dir)].protect == {
        "local": set([re.compile(r"P3.*.jpg")]),
        "recursive": set([re.compile(r"PP.*.jpg")]),
    }

    assert ck.fg.config_files.per_dir_configs[f"{duplicates_dir}/ki"].protect == {
        'local': set(),
        'recursive': set(),
    }

    assert ck.fg.config_files.per_dir_configs[f"{duplicates_dir}/df"].protect == {
        'local': set(),
        'recursive': set(),
    }

    ck.fg.stats()
