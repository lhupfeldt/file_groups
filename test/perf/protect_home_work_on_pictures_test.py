from pathlib import Path
import logging
from timeit import timeit

from guppy import hpy  # type: ignore

from file_groups.groups import FileGroups
from file_groups.config.config_handler import ConfigHandler


_HOME_DIR = Path.home()


def test_basic_collect():
    h = hpy()
    conf_handler = ConfigHandler(ignore_config_dirs_config_files=True, ignore_per_directory_config_files=True)
    exec_time = timeit(lambda: FileGroups([_HOME_DIR/'Documents'], [_HOME_DIR/'Pictures'], config_handler=conf_handler), number=10)
    assert exec_time < 5
    print(h.heap())
    # assert False


def test_debug_basic_collect(caplog):
    caplog.set_level(logging.DEBUG)
    conf_handler = ConfigHandler(ignore_config_dirs_config_files=True, ignore_per_directory_config_files=True)
    exec_time = timeit(lambda: FileGroups([_HOME_DIR/'Documents'], [_HOME_DIR/'Pictures'], config_handler=conf_handler), number=1)
    assert exec_time < 20
