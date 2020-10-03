from pathlib import Path
from timeit import timeit

from guppy import hpy

from file_groups.file_groups import FileGroups


_HOME_DIR = Path.home()


def test_basic_collect():
    h = hpy()
    exec_time = timeit(lambda: FileGroups([_HOME_DIR], [_HOME_DIR/'Pictures']), number=1)
    assert exec_time < 5
    print(h.heap())
    assert False


def test_debug_basic_collect():
    exec_time = timeit(lambda: FileGroups([_HOME_DIR], [_HOME_DIR/'Pictures'], debug=True), number=1)
    assert exec_time < 10
