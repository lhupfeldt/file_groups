import os
from os import DirEntry
from pathlib import Path
from collections import defaultdict
from typing import Any

import pytest

from file_groups.path_display import PathDisplay


@pytest.fixture(name="path_display_check")
def _fixture_path_display_check(home_tilde, rel_path):
    pd = PathDisplay(home_tilde=home_tilde, rel_path=rel_path)

    def check_one(val: Any, exp: Any):
        got = pd.handle_any(val)
        if got == exp or (isinstance(val, set) and isinstance(exp, tuple) and sorted(got) == sorted(exp)):
            return True

        print(f"Type {type(val)}, home_tilde={home_tilde}, rel_path={rel_path}: got {got}, expected {exp}")
        return False

    def check(val: Any, exp_no_mod: Any, *, exp_tilde: Any, exp_rel: Any, exp_rel_tilde: Any = None) -> bool:
        if not home_tilde and not rel_path:
            return check_one(val, exp_no_mod)

        if home_tilde and not rel_path:
            return check_one(val, exp_tilde)

        if not home_tilde and rel_path:
            return check_one(val, exp_rel)

        if home_tilde and rel_path:
            return check_one(val, exp_rel_tilde or exp_rel)

        assert False, "InternalError, we should not get here!"

    return check


@pytest.mark.parametrize("rel_path", [True, False])
@pytest.mark.parametrize("home_tilde", [True, False])
def test_path_display(path_display_check):
    # pylint: disable=too-many-locals
    path = Path(__file__)
    path_exp_abs = str(path)
    path_exp_tilde = path_exp_abs.replace(str(Path.home()), "~")
    path_exp_rel = str(path.relative_to(Path.cwd()))

    assert path_display_check(
        path,
        path_exp_abs,
        exp_tilde=path_exp_tilde, exp_rel=path_exp_rel)

    dir_entry = None
    for dir_entry in os.scandir(path.parent):
        if dir_entry.name == path.name:
            break

    assert path_display_check(
        dir_entry,
        path_exp_abs,
        exp_tilde=path_exp_tilde, exp_rel=path_exp_rel)

    assert path_display_check(
        __file__,
        path_exp_abs,
        exp_tilde=path_exp_tilde, exp_rel=path_exp_rel)

    ex = Exception(f"Two file names in an exception: {__file__} and {Path.home()}/dummy")
    ex_exp_tilde = f"Two file names in an exception: {path_exp_tilde} and ~/dummy"
    ex_exp_rel = f"Two file names in an exception: {path_exp_rel} and {Path.home()}/dummy"
    ex_exp_rel_tilde = f"Two file names in an exception: {path_exp_rel} and ~/dummy"

    assert path_display_check(
        ex,
        str(ex),
        exp_tilde=ex_exp_tilde, exp_rel=ex_exp_rel, exp_rel_tilde=ex_exp_rel_tilde)

    a_list = [path, dir_entry, __file__, ex]
    assert path_display_check(
        a_list,
        [str(path), dir_entry.path, __file__, str(ex)],
        exp_tilde=[path_exp_tilde, path_exp_tilde, path_exp_tilde, ex_exp_tilde],
        exp_rel=[path_exp_rel, path_exp_rel, path_exp_rel, ex_exp_rel],
        exp_rel_tilde=[path_exp_rel, path_exp_rel, path_exp_rel, ex_exp_rel_tilde])

    a_tuple = (path, dir_entry, __file__, ex)
    a_tuple_exp_no_mod = (str(path), dir_entry.path, __file__, str(ex))
    a_tuple_exp_tilde = (path_exp_tilde, path_exp_tilde, path_exp_tilde, ex_exp_tilde)
    a_tuple_exp_rel = (path_exp_rel, path_exp_rel, path_exp_rel, ex_exp_rel)
    a_tuple_exp_rel_tilde = (path_exp_rel, path_exp_rel, path_exp_rel, ex_exp_rel_tilde)

    assert path_display_check(a_tuple, a_tuple_exp_no_mod, exp_tilde=a_tuple_exp_tilde, exp_rel=a_tuple_exp_rel, exp_rel_tilde=a_tuple_exp_rel_tilde)

    a_unique_repr_set = {path, ex}
    assert path_display_check(
        a_unique_repr_set,
        {str(path), str(ex)},
        exp_tilde={path_exp_tilde, ex_exp_tilde},
        exp_rel={path_exp_rel, ex_exp_rel},
        exp_rel_tilde={path_exp_rel, ex_exp_rel_tilde})

    a_set = {path, dir_entry, __file__, ex}
    assert path_display_check(
        a_set,
        (str(path), dir_entry.path, __file__, str(ex)),
        exp_tilde=(path_exp_tilde, path_exp_tilde, path_exp_tilde, ex_exp_tilde),
        exp_rel=(path_exp_rel, path_exp_rel, path_exp_rel, ex_exp_rel),
        exp_rel_tilde=(path_exp_rel, path_exp_rel, path_exp_rel, ex_exp_rel_tilde))

    a_dict = {"path": path, "dir_entry": dir_entry, "__file__": __file__, "ex": ex}
    a_dict_exp_no_mod = {key: (val.path if isinstance(val, DirEntry) else str(val)) for key, val in a_dict.items()}
    a_dict_exp_tilde = {"path": path_exp_tilde, "dir_entry": path_exp_tilde, "__file__": path_exp_tilde, "ex": ex_exp_tilde}
    a_dict_exp_rel = {"path": path_exp_rel, "dir_entry": path_exp_rel, "__file__": path_exp_rel, "ex": ex_exp_rel}
    a_dict_exp_rel_tilde = {"path": path_exp_rel, "dir_entry": path_exp_rel, "__file__": path_exp_rel, "ex": ex_exp_rel_tilde}

    assert path_display_check(a_dict, a_dict_exp_no_mod, exp_tilde=a_dict_exp_tilde, exp_rel=a_dict_exp_rel, exp_rel_tilde=a_dict_exp_rel_tilde)

    nested = {"nested": [a_dict, a_tuple]}
    assert path_display_check(
        nested,
        {"nested": [a_dict_exp_no_mod, a_tuple_exp_no_mod]},
        exp_tilde={"nested": [a_dict_exp_tilde, a_tuple_exp_tilde]},
        exp_rel={"nested": [a_dict_exp_rel, a_tuple_exp_rel]},
        exp_rel_tilde={"nested": [a_dict_exp_rel_tilde, a_tuple_exp_rel_tilde]})


def test_path_display_eq():
    pd1_true_true = PathDisplay(home_tilde=True, rel_path=True)
    pd2_true_true = PathDisplay(home_tilde=True, rel_path=True)
    pd3_true_false = PathDisplay(home_tilde=True, rel_path=False)

    assert pd1_true_true == pd1_true_true  # pylint: disable=comparison-with-itself
    assert pd1_true_true == pd2_true_true
    assert pd1_true_true != pd3_true_false
    assert pd1_true_true != 1


def test_handle_mapping_defaultdict():
    pd = PathDisplay(home_tilde=True, rel_path=True)
    dl: dict[str, list[tuple]] = defaultdict(list)

    dl["a"].append((1, "ttt"))
    assert type(pd.handle_mapping(dl)) == defaultdict  # pylint: disable=unidiomatic-typecheck
