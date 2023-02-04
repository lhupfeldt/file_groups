from __future__ import annotations

import re
import pprint

from file_groups.file_groups import FileGroups

from .conftest import same_content_files
from .utils.file_group_test_utils import FGC
from .config_files_test import set_conf_dirs


@same_content_files("Hejsa", 'ki/Af11.jpg', 'df/Bf11.jpg')
def test_file_groups_sys_user_config_files_no_global(duplicates_dir, set_conf_dirs):
    with FGC(FileGroups(['ki'], ['df'], remember_configs=True, debug=True), duplicates_dir) as ck:
        assert ck.ckfl('must_protect.files', 'ki/Af11.jpg')
        assert ck.ckfl('may_work_on.files', 'df/Bf11.jpg')

    pprint.pprint(ck.fg.config_files.global_config)
    assert ck.fg.config_files.global_config == {
        'file_groups': {
            'protect': {
                'local': set(),
                'recursive': set()
            }
        }
    }

    site_config_dir, user_config_dir = set_conf_dirs
    pprint.pprint(ck.fg.config_files.per_dir_configs)

    assert list(ck.fg.config_files.per_dir_configs.keys()) == [str(site_config_dir), str(user_config_dir), f"{duplicates_dir}/ki", f"{duplicates_dir}/df"]

    assert ck.fg.config_files.per_dir_configs[str(site_config_dir)] == {
        "file_groups": {
            "protect": {
                "local": set([re.compile(r"P1.*\.jpg"), re.compile(r"P2.*\.jpg")]),
                "recursive": set([re.compile(r"PR1.*\.jpg")]),
            },
        },
    }

    assert ck.fg.config_files.per_dir_configs[str(user_config_dir)] == {
        "file_groups": {
            "protect": {
                "local": set([re.compile(r"P3.*.jpg")]),
                "recursive": set([re.compile(r"PP.*.jpg")]),
            }
        }
    }

    assert ck.fg.config_files.per_dir_configs[f"{duplicates_dir}/ki"] == {
        'file_groups': {
            'protect': {
                'local': set(),
                'recursive': set(),
            }
        }
    }

    assert ck.fg.config_files.per_dir_configs[f"{duplicates_dir}/df"] == {
        'file_groups': {
            'protect': {
                'local': set(),
                'recursive': set(),
            }
        }
    }

    ck.fg.stats()
