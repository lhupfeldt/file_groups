import re

import file_groups


def test_version_of_properly_installe_package():
    assert re.match(r"[0-9]+\.[0-9]+\.[0-9]+\..*", file_groups.__version__)
