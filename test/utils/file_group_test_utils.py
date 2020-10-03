import os
from typing import Mapping, List

from file_groups.file_groups import FileGroups


def ckfl(ll, *exp_names):
    """Check file list against expected file names"""
    cwd = os.getcwd()
    got = tuple(sorted(fn.replace(cwd + '/', '') for fn in ll))
    if got == exp_names:
        return True

    print(f"got: {got}")
    print(f"exp: {exp_names}")
    return False


def cksfl(ll, duplicates_dir=None, exp: Mapping[str, List] = None):
    """Check symlink list against expected file names"""
    cwd = os.getcwd()

    if exp is None and not ll:
        return True

    # Turn keys in exp into absolute paths
    exp = {os.path.join(duplicates_dir, path): expl for path, expl in exp.items()}

    for points_to, sym_links in ll.items():
        exp_names = exp.get(points_to)
        if exp_names is None:
            print(f"'points_to' {points_to} not in expected: {exp}")
            return False

        got = sorted(fn.path.replace(cwd + '/', '') for fn in sym_links)
        if got != exp_names:
            print(f"got: {got}")
            print(f"exp: {exp_names}")
            return False

    if len(ll) != len(exp):
        print(f"got: {ll}, exp {exp}")
        return False

    return True


class FGC():
    """File Group Checker - Provide methods for simplified checking of FileGroups."""
    def __init__(self, fg: FileGroups, duplicates_dir):
        self.fg = fg
        self.duplicates_dir = duplicates_dir
        self.checked = set()

    def _ggetattr(self, group_dot_attr):
        group_name, attr_name = group_dot_attr.split('.')
        group = getattr(self.fg, group_name)
        return getattr(group, attr_name)

    def ckfl(self, attr_name, *rel_paths: str):
        self.checked.add(attr_name)
        return ckfl(self._ggetattr(attr_name), *rel_paths)

    def cksfl(self, attr_name, rel_path_to_symlinks: Mapping[str, List[str]]):
        self.checked.add(attr_name)
        return cksfl(self._ggetattr(attr_name), self.duplicates_dir, rel_path_to_symlinks)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_type:
            return

        check_fl = ["must_protect.files", "must_protect.symlinks", "may_work_on.files", "may_work_on.symlinks"]
        check_sfl = ["must_protect.symlinks_by_abs_points_to", "may_work_on.symlinks_by_abs_points_to"]

        for attr_name in check_fl + check_sfl:
            if not attr_name in self.checked:
                print("checking:", attr_name)
                if attr_name.endswith('points_to'):
                    assert cksfl(self._ggetattr(attr_name), self.duplicates_dir, {}), "Not empty '{attr_name}'"
                else:
                    assert ckfl(self._ggetattr(attr_name)), "Not empty '{attr_name}'"
