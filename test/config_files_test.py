import re
from pathlib import Path
import pprint

from appdirs import AppDirs

import pytest

from file_groups.config_files import ConfigFiles

from .conftest import same_content_files


_HERE = Path(__file__).absolute().parent


@pytest.fixture
def set_conf_dirs(request, monkeypatch):
    """Monkey patch appdirs to move the system and user config dirs to test specific directories"""

    test_specific_config_dir_prefix = _HERE/'in/configs'/request.node.name.replace('test_', '')
    print("test_specific_config_dir_prefix:", test_specific_config_dir_prefix)
    assert test_specific_config_dir_prefix.is_dir()

    site_config_dir =  test_specific_config_dir_prefix/'sys'
    monkeypatch.setattr(AppDirs, "site_config_dir", str(site_config_dir))

    user_config_dir = test_specific_config_dir_prefix/'home'
    monkeypatch.setattr(AppDirs, "user_config_dir", str(user_config_dir))

    return site_config_dir, user_config_dir


def dir_conf_files(protect_local, protect_recursive, *conf_files):
    conf = {
        "file_groups": {
            "protect": {
                "local": protect_local,
                "recursive": protect_recursive,
            }
        }
    }

    return same_content_files(repr(conf), *conf_files)


_EXP_GLOBAL_CFG_NO_GLOBAL_PROTECT = {
    'file_groups': {
        'protect': {
            'local': set(),
            'recursive': set()
        }
    }
}


_EXP_SITE_CONFIG_DIR_CFG_NO_GLOBAL_PROTECT = {
    "file_groups": {
        "protect": {
            "local": set([re.compile(r"P1.*\.jpg"), re.compile(r"P2.*\.jpg")]),
            "recursive": set([re.compile(r"PR1.*\.jpg")]),
        },
    },
}


_EXP_USER_CONFIG_DIR_CFG_NO_GLOBAL_PROTECT = {
    "file_groups": {
        "protect": {
            "local": set([re.compile(r"P3.*.jpg")]),
            "recursive": set([re.compile(r"PP.*.jpg")]),
        }
    }
}


def test_config_files_sys_config_file_no_global(set_conf_dirs):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, debug=False)

    pprint.pprint(cfgf.global_config)
    assert cfgf.global_config == _EXP_GLOBAL_CFG_NO_GLOBAL_PROTECT

    site_config_dir, _ = set_conf_dirs
    pprint.pprint(cfgf.per_dir_configs)

    assert list(cfgf.per_dir_configs.keys()) == [str(site_config_dir)]

    assert cfgf.per_dir_configs[str(site_config_dir)] == _EXP_SITE_CONFIG_DIR_CFG_NO_GLOBAL_PROTECT


def test_config_files_user_config_file_no_global(set_conf_dirs):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, debug=False)

    pprint.pprint(cfgf.global_config)
    assert cfgf.global_config == _EXP_GLOBAL_CFG_NO_GLOBAL_PROTECT

    _, user_config_dir = set_conf_dirs
    pprint.pprint(cfgf.per_dir_configs)

    assert list(cfgf.per_dir_configs.keys()) == [str(user_config_dir)]
    assert cfgf.per_dir_configs[str(user_config_dir)] == _EXP_USER_CONFIG_DIR_CFG_NO_GLOBAL_PROTECT


def test_config_files_sys_user_config_files_no_global(set_conf_dirs):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, debug=True)

    pprint.pprint(cfgf.global_config)
    assert cfgf.global_config == _EXP_GLOBAL_CFG_NO_GLOBAL_PROTECT

    site_config_dir, user_config_dir = set_conf_dirs
    pprint.pprint(cfgf.per_dir_configs)

    assert list(cfgf.per_dir_configs.keys()) == [str(site_config_dir), str(user_config_dir)]
    assert cfgf.per_dir_configs[str(site_config_dir)] == _EXP_SITE_CONFIG_DIR_CFG_NO_GLOBAL_PROTECT
    assert cfgf.per_dir_configs[str(user_config_dir)] == _EXP_USER_CONFIG_DIR_CFG_NO_GLOBAL_PROTECT


@dir_conf_files([r'xxx.*xxx', r'yyy.*yyy'], [r'zzz'], 'ddd/.file_groups.conf')
def test_config_files_sys_user_and_and_other_dir_config_files_no_global_no_other_recursive(duplicates_dir, set_conf_dirs):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, debug=False)

    ddd = f"{duplicates_dir}/ddd"
    cfgf.dir_config(Path(ddd), cfgf.global_config)

    pprint.pprint(cfgf.global_config)
    assert cfgf.global_config == _EXP_GLOBAL_CFG_NO_GLOBAL_PROTECT

    site_config_dir, user_config_dir = set_conf_dirs
    pprint.pprint(cfgf.per_dir_configs)

    assert list(cfgf.per_dir_configs.keys()) == [str(site_config_dir), str(user_config_dir), ddd]
    assert cfgf.per_dir_configs[str(site_config_dir)] == _EXP_SITE_CONFIG_DIR_CFG_NO_GLOBAL_PROTECT
    assert cfgf.per_dir_configs[str(user_config_dir)] == _EXP_USER_CONFIG_DIR_CFG_NO_GLOBAL_PROTECT
    assert cfgf.per_dir_configs[ddd] == {
        "file_groups": {
            "protect": {
                "local": set([re.compile(r"xxx.*xxx"), re.compile(r"yyy.*yyy")]),
                "recursive": set([re.compile(r"zzz")]),
            }
        }
    }


def check_inherit_other(cfgf, dupe_dir):
    try:
        ddd1 = f"{dupe_dir}/ddd1"
        ddd2 = f"{ddd1}/ddd2"
        ddd3 = f"{ddd2}/ddd3"

        cfg1, _ = cfgf.dir_config(Path(ddd1), cfgf.global_config)
        cfg2, _ = cfgf.dir_config(Path(ddd2), cfg1)
        cfg3, _ = cfgf.dir_config(Path(ddd3), cfg2)  # ddd3 has no config file

        pprint.pprint(cfgf.per_dir_configs)
        assert list(cfgf.per_dir_configs.keys()) == [ddd1, ddd2, ddd3]

        ddd1_recursive = set([re.compile(r"zzz")])

        assert cfgf.per_dir_configs[ddd1] == cfg1 == {
            "file_groups": {
                "protect": {
                    "local": set([re.compile(r"xxx.*xxx"), re.compile(r"yyy.*yyy")]),
                    "recursive": ddd1_recursive,
                }
            }
        }

        ddd2_recursive = set([re.compile(r"zzz2.*")])
        ddd2_recursive.update(ddd1_recursive)

        assert cfgf.per_dir_configs[ddd2] == cfg2 == {
            "file_groups": {
                "protect": {
                    "local": set([re.compile(r"xxx.*xxx")]),
                    "recursive": ddd2_recursive,
                }
            }
        }

        assert cfgf.per_dir_configs[ddd3] == cfg3 == {
            "file_groups": {
                "protect": {
                    "local": set(),
                    "recursive": ddd2_recursive,
                }
            }
        }

    except AssertionError as ex:
        print(ex)
        return False

    return True


@dir_conf_files([r'xxx.*xxx', r'yyy.*yyy'], [r'zzz'], 'ddd1/.file_groups.conf')
@dir_conf_files([r'xxx.*xxx'], [r'zzz2.*'], 'ddd1/ddd2/.file_groups.conf')
@same_content_files('Hi', 'ddd1/ddd2/ddd3/hi.txt')
def test_config_files_other_dir_config_files_inherit_recursive(duplicates_dir):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, debug=False)
    assert check_inherit_other(cfgf, duplicates_dir)


@dir_conf_files([r'xxx.*xxx', r'yyy.*yyy'], [r'zzz'], 'ddd1/.file_groups.conf')
@dir_conf_files([r'xxx.*xxx'], [r'zzz2.*'], 'ddd1/ddd2/.file_groups.conf')
@same_content_files('Hi', 'ddd1/ddd2/ddd3/hi.txt')
def test_config_files_inherit_ignore_global_recursive(duplicates_dir, set_conf_dirs):
    """We have config dir config files, but we ignore them."""
    cfgf = ConfigFiles(ignore_config_dirs_config_files=True, ignore_per_directory_config_files=False, debug=False)
    assert check_inherit_other(cfgf, duplicates_dir)


def check_inherit_global(cfgf, dupe_dir, conf_dirs):
    try:
        ddd1 = f"{dupe_dir}/ddd1"
        ddd2 = f"{ddd1}/ddd2"
        ddd3 = f"{ddd2}/ddd3"

        cfg1, _ = cfgf.dir_config(Path(ddd1), cfgf.global_config)  # ddd1 has no config file, or it is ignored
        cfg2, _ = cfgf.dir_config(Path(ddd2), cfg1)  # ddd2 has no config file, or it is ignored
        cfg3, _ = cfgf.dir_config(Path(ddd3), cfg2)  # ddd3 has no config file

        global_recursive = set([
            re.compile(r"gsys1.*\.jpg"),
            re.compile(r"gsys2.*\.jpg"),
            re.compile(r"gusr1.*\.jpg"),
        ])

        pprint.pprint(cfgf.global_config)
        assert cfgf.global_config == {
            'file_groups': {
                'protect': {
                    'local': set(),
                    'recursive': global_recursive,
                }
            }
        }

        site_config_dir, user_config_dir = conf_dirs
        print(list(cfgf.per_dir_configs.keys()))
        assert list(cfgf.per_dir_configs.keys()) == [str(site_config_dir), str(user_config_dir), ddd1, ddd2, ddd3]

        ddd1_recursive = set()
        ddd1_recursive.update(global_recursive)

        pprint.pprint(cfgf.per_dir_configs)
        assert cfgf.per_dir_configs[ddd1] == cfg1 == {
            "file_groups": {
                "protect": {
                    "local": set(),
                    "recursive": ddd1_recursive,
                }
            }
        }

        ddd2_recursive = set()
        ddd2_recursive.update(ddd1_recursive)

        assert cfgf.per_dir_configs[ddd2] == cfg2 == {
            "file_groups": {
                "protect": {
                    "local": set(),
                    "recursive": ddd2_recursive,
                }
            }
        }

        assert cfgf.per_dir_configs[ddd3] == cfg3 == {
            "file_groups": {
                "protect": {
                    "local": set(),
                    "recursive": ddd2_recursive,
                }
            }
        }

    except AssertionError as ex:
        print(ex)
        return False

    return True


@same_content_files('Hi', 'ddd1/ddd2/ddd3/hi.txt')
def test_config_files_inherit_global_recursive_no_other(duplicates_dir, set_conf_dirs):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, debug=False)
    assert check_inherit_global(cfgf, duplicates_dir, set_conf_dirs)


@dir_conf_files([r'xxx.*xxx', r'yyy.*yyy'], [r'zzz'], 'ddd1/.file_groups.conf')
@dir_conf_files([r'xxx.*xxx'], [r'zzz2.*'], 'ddd1/ddd2/.file_groups.conf')
@same_content_files('Hi', 'ddd1/ddd2/ddd3/hi.txt')
def test_config_files_inherit_global_recursive_ignore_other(duplicates_dir, set_conf_dirs):
    """We have per directory config files, but we ignore them."""
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=True, debug=False)
    assert check_inherit_global(cfgf, duplicates_dir, set_conf_dirs)


@dir_conf_files([r'xxx.*xxx', r'yyy.*yyy'], [r'zzz'], 'ddd1/.file_groups.conf')
@dir_conf_files([r'xxx.*xxx'], [r'zzz2.*'], 'ddd1/ddd2/.file_groups.conf')
@same_content_files('Hi', 'ddd1/ddd2/ddd3/hi.txt')
def test_config_files_inherit_global_recursive(duplicates_dir, set_conf_dirs):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, debug=False)

    ddd1 = f"{duplicates_dir}/ddd1"
    ddd2 = f"{ddd1}/ddd2"
    ddd3 = f"{ddd2}/ddd3"

    cfg1, _ = cfgf.dir_config(Path(ddd1), cfgf.global_config)
    cfg2, _ = cfgf.dir_config(Path(ddd2), cfg1)
    cfg3, _ = cfgf.dir_config(Path(ddd3), cfg2)  # ddd3 has no config file

    global_recursive = set([
        re.compile(r"gsys1.*\.jpg"),
        re.compile(r"gsys2.*\.jpg"),
        re.compile(r"gusr1.*\.jpg"),
    ])

    pprint.pprint(cfgf.global_config)
    assert cfgf.global_config == {
        'file_groups': {
            'protect': {
                'local': set(),
                'recursive': global_recursive,
            }
        }
    }

    site_config_dir, user_config_dir = set_conf_dirs
    print(list(cfgf.per_dir_configs.keys()))
    assert list(cfgf.per_dir_configs.keys()) == [str(site_config_dir), str(user_config_dir), ddd1, ddd2, ddd3]

    ddd1_recursive = set([re.compile(r"zzz")])
    ddd1_recursive.update(global_recursive)

    pprint.pprint(cfgf.per_dir_configs)
    assert cfgf.per_dir_configs[ddd1] == cfg1 == {
        "file_groups": {
            "protect": {
                "local": set([re.compile(r"xxx.*xxx"), re.compile(r"yyy.*yyy")]),
                "recursive": ddd1_recursive,
            }
        }
    }

    ddd2_recursive = set([re.compile(r"zzz2.*")])
    ddd2_recursive.update(ddd1_recursive)

    assert cfgf.per_dir_configs[ddd2] == cfg2 == {
        "file_groups": {
            "protect": {
                "local": set([re.compile(r"xxx.*xxx")]),
                "recursive": ddd2_recursive,
            }
        }
    }

    assert cfgf.per_dir_configs[ddd3] == cfg3 == {
        "file_groups": {
            "protect": {
                "local": set(),
                "recursive": ddd2_recursive,
            }
        }
    }



# ---------- Errors ----------

def test_config_files_two_in_same_config_dir(set_conf_dirs):
    with pytest.raises(Exception) as exinfo:
        ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, debug=False)

    _, user_config_dir = set_conf_dirs
    assert f"More than one config file in dir '{user_config_dir}': ['.file_groups.conf', 'file_groups.conf']" in str(exinfo.value)


@dir_conf_files([r'xxx.*xxx', r'yyy.*yyy'], [r'zzz'], 'ddd/.file_groups.conf', 'ddd/file_groups.conf')
def test_config_files_two_in_same_other_dir(duplicates_dir):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, debug=False)

    with pytest.raises(Exception) as exinfo:
        ddd = f"{duplicates_dir}/ddd"
        cfgf.dir_config(Path(ddd), cfgf.global_config)

    assert f"More than one config file in dir '{duplicates_dir}/ddd': ['.file_groups.conf', 'file_groups.conf']" in str(exinfo.value)


@same_content_files(repr({"filegroups": {}}), 'ddd/file_groups.conf')
def test_config_files_missing_file_groups_key(duplicates_dir):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, debug=False)

    with pytest.raises(Exception) as exinfo:
        ddd = f"{duplicates_dir}/ddd"
        cfgf.dir_config(Path(ddd), cfgf.global_config)

    assert f"Config file '{duplicates_dir}/ddd/file_groups.conf' is missing mandatory configuration 'file_groups[protect]'" in str(exinfo.value)


@same_content_files(repr({"file_groups": {"potect": {}}}), 'ddd/file_groups.conf')
def test_config_files_missing_protect_key(duplicates_dir):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, debug=False)

    with pytest.raises(Exception) as exinfo:
        ddd = f"{duplicates_dir}/ddd"
        cfgf.dir_config(Path(ddd), cfgf.global_config)

    assert f"Config file '{duplicates_dir}/ddd/file_groups.conf' is missing mandatory configuration 'file_groups[protect]'" in str(exinfo.value)


def test_config_files_unknown_protect_sub_key_config_dir(set_conf_dirs):
    with pytest.raises(Exception) as exinfo:
        ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, debug=False)

    sys_config_dir, _ = set_conf_dirs
    exp = f"The only keys allowed in 'file_groups[protect]' section in the config file '{sys_config_dir}/file_groups.conf' are: ('local', 'recursive', 'global'). "
    exp += "Got: 'gobal'"
    assert exp in str(exinfo.value)


@same_content_files(repr({"file_groups": {"protect": {"hola": r"X"}}}), 'ddd/file_groups.conf')
def test_config_files_unknown_protect_sub_key_other_dir(duplicates_dir):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, debug=False)

    with pytest.raises(Exception) as exinfo:
        ddd = f"{duplicates_dir}/ddd"
        cfgf.dir_config(Path(ddd), cfgf.global_config)

    exp = f"The only keys allowed in 'file_groups[protect]' section in the config file '{duplicates_dir}/ddd/file_groups.conf' are: ('local', 'recursive'). "
    exp += "Got: 'hola'."
    assert exp in str(exinfo.value)


@same_content_files(repr({"file_groups": {"protect": {"local": r"X", "global": r"X"}}}), 'ddd/.file_groups.conf')
def test_config_files_invalid_protect_global_key_other_dir(duplicates_dir):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, debug=False)

    with pytest.raises(Exception) as exinfo:
        ddd = f"{duplicates_dir}/ddd"
        cfgf.dir_config(Path(ddd), cfgf.global_config)

    exp = f"The only keys allowed in 'file_groups[protect]' section in the config file '{duplicates_dir}/ddd/.file_groups.conf' are: ('local', 'recursive'). "
    exp += "Got: 'global'."
    assert exp in str(exinfo.value)
