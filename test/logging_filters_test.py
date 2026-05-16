import sys
import os
import logging
from pathlib import Path

import pytest

from file_groups.logging_filters import PathFilter


@pytest.mark.parametrize("rel_path", [True, False])
@pytest.mark.parametrize("home_tilde", [True, False])
def test_path_filter(home_tilde, rel_path, capsys):
    path = Path(__file__)

    # Note: use capsys instead of caplog because of 'logging' module global state
    # This test cannot run twice (or with home_tilde False?) when other tests are also run if caplog is used.

    # root_logger = logging.getLogger()
    # for handler in root_logger.handlers.copy():
    #     print(handler)
    #     print(handler.filters)

    log = logging.getLogger(f"{path.name}-{home_tilde}-{rel_path}")
    log.addHandler(logging.StreamHandler(sys.stdout))
    log.addFilter(PathFilter(home_tilde=home_tilde, rel_path=rel_path))
    log.propagate = False

    dir_entry = None
    for dir_entry in os.scandir(path.parent):
        if dir_entry.name == path.name:
            break

    ex = Exception(f"Two file names in an exception: {__file__} and {Path.home()}/dummy")

    log.error("Path %s", path)
    log.error("DirEntry %s", dir_entry)
    log.error("str %s", __file__)
    log.error("Exception %s", ex)
    log.error("set %s", {path, dir_entry, __file__, ex})
    log.error("list %s", [path, dir_entry, __file__, ex])
    log.error("tuple %s", (path, dir_entry, __file__, ex))
    log.error("dict %s", {"path": path, "dir_entry": dir_entry, "__file__": __file__, "ex": ex})

    sout, _ = capsys.readouterr()
    if home_tilde:
        assert "~" in sout
        assert str(Path.home()) not in sout
    else:
        assert str(Path.home()) in sout
        assert "~" not in sout
