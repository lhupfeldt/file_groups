import os
from os import DirEntry
from pathlib import Path
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, Dict, List, Sequence, Set


@dataclass
class _Group():
    name: str

    dirs: Dict[str, Path]

    files: Dict[str, DirEntry]
    symlinks: Dict[str, DirEntry]
    symlinks_by_abs_points_to: Dict[str, List[DirEntry]]

    num_directories: int = 0
    num_directory_symlinks: int = 0

    def add_entry_match(self, entry, *, debug):
        """Abstract, but abstract and dataclass does not work with mypy. https://github.com/python/mypy/issues/500"""

@dataclass
class _IncludeMatchGroup(_Group):
    include: Optional[re.Pattern] = None  # pylint: disable=unsubscriptable-object

    def add_entry_match(self, entry, *, debug):
        if not self.include:
            self.files[entry.path] = entry
            return

        match = self.include.match(entry.name)
        if debug:
            print(f' - include {self.include} match {match}')

        if match:
            self.files[entry.path] = entry


@dataclass
class _ExcludeMatchGroup(_Group):
    exclude: Optional[re.Pattern] = None  # pylint: disable=unsubscriptable-object

    def add_entry_match(self, entry, *, debug):
        if not self.exclude:
            self.files[entry.path] = entry
            return

        match = self.exclude.match(entry.name)
        if debug:
            print(f' - exclude {self.exclude} match {match}')

        if not match:
            self.files[entry.path] = entry


class FileGroups():
    """Create six different groups of regular files and symlinks.

    Arguments:
        protect_dirs_seq: Directories in which (regular) files may not be deleted/modified.
            Directory may be a subdirectory of (or the same, for convenient globbing) as a work_dirs_seq directory.

        work_dirs_seq: Directories in which to potentially delete/modify files.
            Directory may be a subdirectory of (or the same, for convenient globbing) as a protect_dirs_seq directory.

        protect_exclude: Exclude files matching regex in the protected files (does not apply to symlinks). Default NONE (include ALL).
        work_include: Only include files matching regex in the may_work_on files (does not apply to symlinks). Default include ALL.

    Note that symlinks are followed for the specified arguments, but never for any subdirectories.
        debug: Be extremely verbose.
    """

    def __init__(
            self,
            protect_dirs_seq: Sequence[Path], work_dirs_seq: Sequence[Path],
            *,
            protect_exclude: re.Pattern = None, work_include: re.Pattern = None,
            debug=False):
        super().__init__()
        self.debug = debug

        # Turn all paths into absolute paths with symlinks resolved, keep referrence to original argument for messages
        protect_dirs: Dict[str, Path] = {os.path.abspath(os.path.realpath(kp)): kp for kp in protect_dirs_seq}

        work_dirs: Dict[str, Path] = {}
        for dp in work_dirs_seq:
            real_dp = os.path.abspath(os.path.realpath(dp))
            if real_dp in protect_dirs:
                specified_protect_dir = protect_dirs[real_dp]

                if dp == specified_protect_dir:
                    print(f"Ignoring 'work' dir '{dp}' which is also a 'protect' dir.")
                    continue

                print(f"Ignoring 'work' dir '{real_dp}' (from argument '{dp}') which is also a 'protect' dir (from argument '{specified_protect_dir}').")
                continue

            work_dirs[real_dp] = dp

        self.must_protect = _ExcludeMatchGroup('must_protect', protect_dirs, {}, {}, defaultdict(list), exclude=protect_exclude)
        self.may_work_on = _IncludeMatchGroup('may_work_on', work_dirs, {}, {}, defaultdict(list), include=work_include)

        self.collect()

    def collect(self):
        """Split files into groups.

        E.g.:

            Given:

            top/d1
            top/d1/d1
            top/d1/d1/f1.jpg
            top/d1/d1/f2.jpg
            top/d1/d1/f2.JPG
            top/d1/d2
            top/d1/d2/f1.jpg
            top/d1/d2/f2.jpg
            top/d1/f1.jpg
            top/d1/f2.jpg
            top/d2
            top/d2/d1
            top/d2/d1/f1.jpg

            When: self.work_dirs_seq is [top, top/d1/d1]
            And: self.protect_dirs_seq is [top/d1]

            Then:

            Must protect:
            top/d1/d2/f1.jpg
            top/d1/d2/f2.jpg
            top/d1/f1.jpg
            top/d1/f2.jpg

            May work_on:
            top/d1/d1/f1.jpg
            top/d1/d1/f2.jpg
            top/d1/d1/f2.JPG
            top/d2/d1/f1.jpg

        This is called from __init__(), so there would normally be no need to call this explicitly.
        """

        def trace(*args, **kwargs):
            if self.debug:
                print(*args, **kwargs)

        checked_dirs: Set[str] = set()

        def find_group(abs_dir_path: str, group: _Group, other_group: _Group):
            """Find all files belonging to 'group'"""
            trace(f'find {group.name}:', abs_dir_path)
            if abs_dir_path in checked_dirs:
                trace('directory already checked')
                return

            group.num_directories += 1

            for entry in os.scandir(abs_dir_path):
                if entry.is_dir(follow_symlinks=False):
                    if entry.path in other_group.dirs:
                        trace(f"find {group.name} - '{entry.path}' is in '{other_group.name}' dir list and not in '{group.name}' dir list")
                        find_group(entry.path, other_group, group)
                        continue

                    find_group(entry.path, group, other_group)
                    continue

                if entry.is_symlink():
                    points_to = os.readlink(entry)
                    abs_points_to = os.path.normpath(os.path.join(abs_dir_path, points_to))

                    if entry.is_dir(follow_symlinks=True):
                        trace(f"find {group.name} - '{entry.path}' -> '{points_to}' is a symlink to a directory - ignoring")
                        group.num_directory_symlinks += 1
                        continue

                    group.symlinks[entry.path] = entry
                    group.symlinks_by_abs_points_to[abs_points_to].append(entry)
                    continue

                trace(f'find {group.name} - entry name: {entry.name}')
                group.add_entry_match(entry, debug=self.debug)

            checked_dirs.add(abs_dir_path)

        for kip in self.must_protect.dirs:
            find_group(kip, self.must_protect, self.may_work_on)

        for dfp in self.may_work_on.dirs:
            find_group(dfp, self.may_work_on, self.must_protect)

    def dump(self):
        """Print collected files. This may be A LOT of output for large directories."""

        print()

        print('must protect:')
        for path in self.must_protect.files:
            print(path)
        print()

        print('must protect symlinks:')
        for path in self.must_protect.symlinks:
            print(path, '->', os.readlink(path))
        print()

        print('must protect symlinks by absolute points to:')
        for abs_points_to, ee in self.must_protect.symlinks_by_abs_points_to.items():
            print(ee, '->', abs_points_to)
        print()

        print('may work on:')
        for path in self.may_work_on.files:
            print(path)
        print()

        print('may work on symlinks:')
        for path in self.may_work_on.symlinks:
            print(path, '->', os.readlink(path))
        print()

        print('may work on symlinks by absolute points to:')
        for abs_points_to, ee in self.may_work_on.symlinks_by_abs_points_to.items():
            print(ee, '->', abs_points_to)
        print()

        print()

    def stats(self):
        print('collected protect_directories:', self.must_protect.num_directories)
        print('collected protect_directory_symlinks:', self.must_protect.num_directory_symlinks)
        print('collected work_on_directories:', self.may_work_on.num_directories)
        print('collected work_on_directory_symlinks:', self.may_work_on.num_directory_symlinks)

        print('collected must_protect_files:', len(self.must_protect.files))
        print('collected must_protect_symlinks:', len(self.must_protect.symlinks))
        print('collected may_work_on_files:', len(self.may_work_on.files))
        print('collected may_work_on_symlinks:', len(self.may_work_on.symlinks))
