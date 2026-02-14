import re
from pathlib import Path
import json
import pprint
import logging

from appdirs import AppDirs

import pytest

from file_groups.config.dir_config import DirConfig
from file_groups.config.files import ConfigFiles

from ..conftest import same_content_files, dir_conf_files


_HERE = Path(__file__).absolute().parent
_CONFIGS_DIR = _HERE.parent/'in/configs'

_EXP_GLOBAL_CFG_NO_GLOBAL_PROTECT_RECURSIVE =  set()

_EXP_SITE_CONFIG_DIR_CFG_NO_GLOBAL_PROTECT = (set([re.compile(r"P1.*\.jpg"), re.compile(r"P2.*\.jpg")]), set([re.compile(r"PR1.*\.jpg")]))
_EXP_USER_CONFIG_DIR_CFG_NO_GLOBAL_PROTECT = (set([re.compile(r"P3.*.jpg")]), set([re.compile(r"PP.*.jpg")]))


class MyEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, '__json__'):
            return o.__json__()
        if isinstance(o, set):
            return [self.default(elt) for elt in o]
        if isinstance(o, re.Pattern):
            return str(o)
        if isinstance(o, Path):
            return repr(o)
        return super().default(o)


_PP = pprint.PrettyPrinter(indent=2, width=200)

def _pp(msg, obj):
    print(msg)
    try:
        if isinstance(obj, dict):
            obj = {repr(key): val for key, val in obj.items()}
        print(json.dumps(obj, indent=2, cls=MyEncoder))
    except TypeError:
        _PP.pprint(obj)


@pytest.fixture
def set_conf_dirs(request, monkeypatch):
    """Monkey patch appdirs to move the system and user config dirs to test specific directories"""

    func_name, _, _ = request.node.name.partition('[')
    test_specific_config_dir_prefix = _CONFIGS_DIR/func_name.replace('test_', '')
    print("test_specific_config_dir_prefix:", test_specific_config_dir_prefix)
    assert test_specific_config_dir_prefix.is_dir()

    site_config_dir =  test_specific_config_dir_prefix/'sys'
    monkeypatch.setattr(AppDirs, "site_config_dir", str(site_config_dir))

    user_config_dir = test_specific_config_dir_prefix/'home'
    monkeypatch.setattr(AppDirs, "user_config_dir", str(user_config_dir))

    return site_config_dir, user_config_dir


def app_dirs_conf_files(protect_local, protect_recursive, protect_global, *conf_files):
    conf = {
        "file_groups": {
            "protect": {
                "local": protect_local,
                "recursive": protect_recursive,
                "global": protect_global,
            }
        }
    }

    return same_content_files(repr(conf), *conf_files)


def _mk_global_dir_conf(patterns: set[re.Pattern]) -> DirConfig:
    return DirConfig(patterns, set(), None, [])


def _mk_empty_dir_conf() -> DirConfig:
    return _mk_global_dir_conf(set())


# pylint: disable=protected-access

def test_config_files_sys_config_file_no_global(set_conf_dirs, log_debug):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False)
    cfgf.load_config_dir_files()

    _pp("cfgf.global_config", cfgf.global_config)
    assert cfgf.global_config.protect_recursive == _EXP_GLOBAL_CFG_NO_GLOBAL_PROTECT_RECURSIVE

    assert "Merged global config:" in log_debug.text
    exp = {'file_groups': {'protect': {'local': {re.compile('P1.*\\.jpg'),
                                                 re.compile('P2.*\\.jpg')},
                                       'recursive': {re.compile('PR1.*\\.jpg')}}}}
    assert pprint.pformat(exp) in log_debug.text


def test_config_files_user_config_file_no_global(set_conf_dirs):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False)
    cfgf.load_config_dir_files()

    _pp("cfgf.global_config:", cfgf.global_config)
    assert cfgf.global_config.protect_recursive == _EXP_GLOBAL_CFG_NO_GLOBAL_PROTECT_RECURSIVE


@pytest.mark.parametrize("app_dirs", [None, (ConfigFiles.default_appdirs, AppDirs("ttt", "Hurra"))])
def test_config_files_sys_user_config_files_no_global(set_conf_dirs, app_dirs, log_debug):
    """No ttt config exists"""
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, app_dirs=app_dirs)
    cfgf.load_config_dir_files()

    _pp("cfgf.global_config:", cfgf.global_config)
    assert cfgf.global_config.protect_recursive == _EXP_GLOBAL_CFG_NO_GLOBAL_PROTECT_RECURSIVE

    print(log_debug.text)


def test_config_files_sys_user_config_files_additional_appdirs(set_conf_dirs, log_debug):
    app_dirs = (ConfigFiles.default_appdirs, AppDirs("an_app", "This is an application using the awesome file_groups!"))
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, app_dirs=app_dirs)
    cfgf.load_config_dir_files()

    _pp("cfgf.global_config:", cfgf.global_config)
    assert cfgf.global_config == _mk_global_dir_conf(set([re.compile(r'FFF.*\.jpeg'), re.compile(r'GGG.*\.mov'), re.compile(r'PP.*\.jpg')]))


def test_config_files_sys_user_config_files_replaced_appdirs(set_conf_dirs, log_debug):
    app_dirs = (AppDirs("an_app", "Yeah!"),)
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, app_dirs=app_dirs)
    cfgf.load_config_dir_files()

    _pp("cfgf.global_config:", cfgf.global_config)
    assert cfgf.global_config == _mk_global_dir_conf(set([re.compile(r'FFF.*\.jpeg'), re.compile(r'GGG.*\.mov')]))


@dir_conf_files([r'xxx.*xxx', r'yyy.*yyy'], [r'zzz'], 'ddd/.file_groups.conf')
def test_config_files_sys_user_and_and_other_dir_config_files_no_global_no_other_recursive(duplicates_dir, set_conf_dirs, caplog):
    caplog.set_level(logging.DEBUG)
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False)
    cfgf.load_config_dir_files()

    ddd = duplicates_dir/"ddd"
    ddd_cfg = cfgf.dir_config(ddd, cfgf.global_config)
    assert ddd_cfg == DirConfig(set([re.compile(r"zzz")]), set([re.compile(r"xxx.*xxx"), re.compile(r"yyy.*yyy")]), ddd, [".file_groups.conf"])

    _pp("cfgf.global_config:", cfgf.global_config)
    assert cfgf.global_config.protect_recursive == _EXP_GLOBAL_CFG_NO_GLOBAL_PROTECT_RECURSIVE


def check_inherit_other(cfgf, dupe_dir):
    try:
        ddd1 = dupe_dir/"ddd1"
        ddd2 = ddd1/"ddd2"
        ddd3 = ddd2/"ddd3"

        cfg1 = cfgf.dir_config(ddd1, _mk_empty_dir_conf())
        cfg2 = cfgf.dir_config(ddd2, cfg1)
        cfg3 = cfgf.dir_config(ddd3, cfg2)  # ddd3 has no config file

        ddd1_recursive = set([re.compile(r"zzz")])

        assert cfg1.protect_local == set([re.compile(r"xxx.*xxx"), re.compile(r"yyy.*yyy")])
        assert cfg1.protect_recursive == ddd1_recursive

        ddd2_recursive = set([re.compile(r"zzz2.*")])
        ddd2_recursive.update(ddd1_recursive)

        assert cfg2.protect_local == set([re.compile(r"xxx.*xxx")])
        assert cfg2.protect_recursive == ddd2_recursive

        assert cfg3.protect_local == set()
        assert cfg3.protect_recursive == ddd2_recursive

    except AssertionError as ex:
        print(ex)
        return False

    return True


@dir_conf_files([r'xxx.*xxx', r'yyy.*yyy'], [r'zzz'], 'ddd1/.file_groups.conf')
@dir_conf_files([r'xxx.*xxx'], [r'zzz2.*'], 'ddd1/ddd2/.file_groups.conf')
@same_content_files('Hi', 'ddd1/ddd2/ddd3/hi.txt')
def test_config_files_other_dir_config_files_inherit_recursive(duplicates_dir, log_debug):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False)
    try:
        assert check_inherit_other(cfgf, duplicates_dir)

        assert "Merged directory config:" in log_debug.text
        exp = {'file_groups': {'protect': {'local': {re.compile('yyy.*yyy'),
                                                     re.compile('xxx.*xxx')},
                                           'recursive': {re.compile('zzz')}}}}
        assert pprint.pformat(exp) in log_debug.text
    except AssertionError:
        print(log_debug.text)
        raise


@dir_conf_files([r'xxx.*xxx', r'yyy.*yyy'], [r'zzz'], 'ddd1/.file_groups.conf')
@dir_conf_files([r'xxx.*xxx'], [r'zzz2.*'], 'ddd1/ddd2/.file_groups.conf')
@same_content_files('Hi', 'ddd1/ddd2/ddd3/hi.txt')
def test_config_files_inherit_ignore_global_recursive(duplicates_dir, set_conf_dirs):
    """We have config dir config files, but we ignore them."""
    cfgf = ConfigFiles(ignore_config_dirs_config_files=True, ignore_per_directory_config_files=False)
    assert check_inherit_other(cfgf, duplicates_dir)


def check_inherit_global(cfgf, dupe_dir):
    try:
        ddd1 = dupe_dir/"ddd1"
        ddd2 = ddd1/"ddd2"
        ddd3 = ddd2/"ddd3"

        global_recursive = set([
            re.compile(r"gsys1.*\.jpg"),
            re.compile(r"gsys2.*\.jpg"),
            re.compile(r"gusr1.*\.jpg"),
        ])

        cfg1 = cfgf.dir_config(ddd1, _mk_global_dir_conf(global_recursive))  # ddd1 has no config file, or it is ignored
        cfg2 = cfgf.dir_config(ddd2, cfg1)  # ddd2 has no config file, or it is ignored
        cfg3 = cfgf.dir_config(ddd3, cfg2)  # ddd3 has no config file

        _pp("cfgf.global_config:", cfgf.global_config)

        assert cfgf.global_config.protect_recursive == global_recursive, f"recursive mismatch: {global_recursive}"

        ddd1_recursive = set()
        ddd1_recursive.update(global_recursive)

        assert cfg1.protect_local == set(), f"cfg1.protect_local is not empty: {cfg1.protect_local}"
        assert cfg1.protect_recursive == ddd1_recursive, f"cfg1.protect_recursive != {ddd1_recursive}"

        ddd2_recursive = set()
        ddd2_recursive.update(ddd1_recursive)

        assert cfg2.protect_local == set(), f"cfg2.protect_local is not empty: {cfg2.protect_local}"
        assert cfg2.protect_recursive == ddd2_recursive, f"cfg2.protect_recursive != {ddd2_recursive}"

        assert cfg3.protect_local == set(), f"cfg3.protect_local is not empty: {cfg3.protect_local}"
        assert cfg3.protect_recursive == ddd2_recursive, f"cfg3.protect_recursive != {ddd2_recursive}"

    except AssertionError as ex:
        print(ex)
        return False

    return True


@same_content_files('Hi', 'ddd1/ddd2/ddd3/hi.txt')
def test_config_files_inherit_global_recursive_no_other(duplicates_dir, set_conf_dirs):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False)
    cfgf.load_config_dir_files()
    assert check_inherit_global(cfgf, duplicates_dir)


@dir_conf_files([r'xxx.*xxx', r'yyy.*yyy'], [r'zzz'], 'ddd1/.file_groups.conf')
@dir_conf_files([r'xxx.*xxx'], [r'zzz2.*'], 'ddd1/ddd2/.file_groups.conf')
@same_content_files('Hi', 'ddd1/ddd2/ddd3/hi.txt')
def test_config_files_inherit_global_recursive_ignore_other(duplicates_dir, set_conf_dirs):
    """We have per directory config files, but we ignore them."""
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=True)
    cfgf.load_config_dir_files()
    assert check_inherit_global(cfgf, duplicates_dir)


@dir_conf_files([r'xxx.*xxx', r'yyy.*yyy'], [r'zzz'], 'ddd1/.file_groups.conf')
@dir_conf_files([r'xxx.*xxx'], [r'zzz2.*'], 'ddd1/ddd2/.file_groups.conf')
@same_content_files('Hi', 'ddd1/ddd2/ddd3/hi.txt')
def test_config_files_inherit_global_recursive(duplicates_dir, set_conf_dirs):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False)
    cfgf.load_config_dir_files()

    ddd1 = duplicates_dir/"ddd1"
    ddd2 = ddd1/"ddd2"
    ddd3 = ddd2/"ddd3"

    cfg1 = cfgf.dir_config(ddd1, cfgf.global_config)
    cfg2 = cfgf.dir_config(ddd2, cfg1)
    cfg3 = cfgf.dir_config(ddd3, cfg2)  # ddd3 has no config file

    global_recursive = set([
        re.compile(r"gsys1.*\.jpg"),
        re.compile(r"gsys2.*\.jpg"),
        re.compile(r"gusr1.*\.jpg"),
    ])

    _pp("cfgf.global_config:", cfgf.global_config)
    assert cfgf.global_config.protect_recursive == global_recursive

    ddd1_recursive = set([re.compile(r"zzz")])
    ddd1_recursive.update(global_recursive)

    assert cfg1.protect_local == set([re.compile(r"xxx.*xxx"), re.compile(r"yyy.*yyy")])
    assert cfg1.protect_recursive == ddd1_recursive

    ddd2_recursive = set([re.compile(r"zzz2.*")])
    ddd2_recursive.update(ddd1_recursive)

    assert cfg2.protect_local == set([re.compile(r"xxx.*xxx")])
    assert cfg2.protect_recursive == ddd2_recursive

    assert cfg3.protect_local == set()
    assert cfg3.protect_recursive == ddd2_recursive


def test_config_files_specified(request, log_debug):
    func_name, _, _ = request.node.name.partition('[')
    config_file = _CONFIGS_DIR/func_name.replace('test_', '')/"direct.conf"
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, config_file=config_file)
    cfgf.load_config_dir_files()

    assert "Merged directory config:" in log_debug.text

    _pp("cfgf.global_config:", cfgf.global_config)
    assert cfgf.global_config == _mk_global_dir_conf(set([re.compile(r"gusr1.*\.jpg")]))
    # TODO: should we have dir(s) and files in global DirConfig?


# ---------- Errors ----------

def test_config_files_two_in_same_config_dir(set_conf_dirs):
    with pytest.raises(Exception) as exinfo:
        cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False)
        cfgf.load_config_dir_files()

    _, user_config_dir = set_conf_dirs
    assert f"More than one config file in dir '{user_config_dir}': ['file_groups.conf', '.file_groups.conf']" in str(exinfo.value)


@dir_conf_files([r'xxx.*xxx', r'yyy.*yyy'], [r'zzz'], 'ddd/.file_groups.conf', 'ddd/file_groups.conf')
def test_config_files_two_in_same_other_dir(duplicates_dir):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False)

    with pytest.raises(Exception) as exinfo:
        ddd = f"{duplicates_dir}/ddd"
        cfgf.dir_config(Path(ddd), cfgf.global_config)

    assert f"More than one config file in dir '{duplicates_dir}/ddd': ['file_groups.conf', '.file_groups.conf']" in str(exinfo.value)


@same_content_files(repr({"filegroups": {}}), 'ddd/file_groups.conf')
def test_config_files_missing_file_groups_key(duplicates_dir):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False)

    with pytest.raises(Exception) as exinfo:
        ddd = f"{duplicates_dir}/ddd"
        cfgf.dir_config(Path(ddd), cfgf.global_config)

    assert f"Config file '{duplicates_dir}/ddd/file_groups.conf' is missing mandatory configuration 'file_groups[protect]'" in str(exinfo.value)


@same_content_files(repr({"file_groups": {"potect": {}}}), 'ddd/file_groups.conf')
def test_config_files_missing_protect_key(duplicates_dir):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False)

    with pytest.raises(Exception) as exinfo:
        ddd = f"{duplicates_dir}/ddd"
        cfgf.dir_config(Path(ddd), cfgf.global_config)

    assert f"Config file '{duplicates_dir}/ddd/file_groups.conf' is missing mandatory configuration 'file_groups[protect]'" in str(exinfo.value)


def test_config_files_unknown_protect_sub_key_config_dir(set_conf_dirs):
    with pytest.raises(Exception) as exinfo:
        cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False)
        cfgf.load_config_dir_files()

    sys_config_dir, _ = set_conf_dirs
    exp = f"The only keys allowed in 'file_groups[protect]' section in the config file '{sys_config_dir}/file_groups.conf' are: ('local', 'recursive', 'global'). "
    exp += "Got: 'gobal'"
    assert exp in str(exinfo.value)


@same_content_files(repr({"file_groups": {"protect": {"hola": r"X"}}}), 'ddd/file_groups.conf')
def test_config_files_unknown_protect_sub_key_other_dir(duplicates_dir):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False)

    with pytest.raises(Exception) as exinfo:
        ddd = f"{duplicates_dir}/ddd"
        cfgf.dir_config(Path(ddd), cfgf.global_config)

    exp = f"The only keys allowed in 'file_groups[protect]' section in the config file '{duplicates_dir}/ddd/file_groups.conf' are: ('local', 'recursive'). "
    exp += "Got: 'hola'."
    assert exp in str(exinfo.value)


@same_content_files(repr({"file_groups": {"protect": {"local": r"X", "global": r"X"}}}), 'ddd/.file_groups.conf')
def test_config_files_invalid_protect_global_key_other_dir(duplicates_dir):
    cfgf = ConfigFiles(ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False)

    with pytest.raises(Exception) as exinfo:
        ddd = f"{duplicates_dir}/ddd"
        cfgf.dir_config(Path(ddd), cfgf.global_config)

    exp = f"The only keys allowed in 'file_groups[protect]' section in the config file '{duplicates_dir}/ddd/.file_groups.conf' are: ('local', 'recursive'). "
    exp += "Got: 'global'."
    assert exp in str(exinfo.value)


def test_config_files_not_existing_specified():
    config_file = Path("xxx.conf")
    cfgf = ConfigFiles(ignore_config_dirs_config_files=True, ignore_per_directory_config_files=True, config_file=config_file)

    with pytest.raises(FileNotFoundError) as exinfo:
        cfgf.load_config_dir_files()

    assert str(config_file) in str(exinfo.value)
