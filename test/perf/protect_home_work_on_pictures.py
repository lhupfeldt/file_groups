from pathlib import Path
import logging
from timeit import timeit

from guppy import hpy  # type: ignore

from file_groups.groups import FileGroups


_HOME_DIR = Path.home()


def test_basic_collect():
    h = hpy()
    exec_time = timeit(lambda: FileGroups([_HOME_DIR], [_HOME_DIR/'Pictures']), number=1)
    assert exec_time < 5
    print(h.heap())
    assert False


def test_debug_basic_collect(caplog):
    caplog.set_level(logging.DEBUG)
    exec_time = timeit(lambda: FileGroups([_HOME_DIR], [_HOME_DIR/'Pictures']), number=1)
    assert exec_time < 10
