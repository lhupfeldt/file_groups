import os
from os import DirEntry
from pathlib import Path
import re
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import chain
from enum import Enum
import logging
from pprint import pformat
from typing import Self, Sequence, Iterator, cast

from .path_display import PathDisplay
from .config.dir_config import DirConfig
from .config.config_handler import ConfigHandler


_LOG = logging.getLogger(__name__)


class GroupType(Enum):
    """Define the file group types."""
    MUST_PROTECT = 0
    MAY_WORK_ON = 1


@dataclass
class _Entries():
    files: dict[str, DirEntry] = field(default_factory=dict)
    symlinks: dict[str, DirEntry] = field(default_factory=dict)

    # For stats only
    num_directory_symlinks: int = 0


class DirGroups(_Entries):
    """Create different groups of regular files and symlinks by collecting files under a directory.

    Arguments:
        root_file_groups: The top level collection and argument handling class.
        abs_dir_path: The absolute path to the directory.
    """

    def __init__(self, typ: GroupType, root_file_groups: "FileGroups", rel_dir_path: Path, parent: Self|"FileGroups"):
        super().__init__()
        self.typ = typ
        self.root_file_groups = root_file_groups
        self.rel_dir_path = rel_dir_path
        self.abs_dir_path: Path = parent.abs_dir_path / rel_dir_path
        self.dir_config: DirConfig = root_file_groups.config_handler.config_file_loader.load_dir_config(self.abs_dir_path, parent.dir_config)
        self.include_exclude = root_file_groups.protect_exclude if self.typ == GroupType.MUST_PROTECT else root_file_groups.work_include

        self.other = _Entries()

    def handle_entry(self, entry: DirEntry) -> None:
        """Put entry in  the correct group. Call 'collect' if entry is a directory."""
        pattern = self.dir_config.is_protected(entry) if self.typ is GroupType.MAY_WORK_ON else None

        if entry.is_dir(follow_symlinks=False):
            abs_dir_path = str(Path(entry.path).resolve())
            arg_dir = self.root_file_groups.dirs.get(abs_dir_path)
            if arg_dir:
                _LOG.debug("'%s' is already in dirs (from args)", entry.path)
                arg_dir.collect()
                return

            dir_grp = DirGroups(GroupType.MUST_PROTECT if pattern else self.typ, self.root_file_groups, entry.path, self)
            self.root_file_groups.dirs[abs_dir_path] = dir_grp
            dir_grp.collect()
            return

        if entry.name in self.root_file_groups.config_handler.conf_file_names:
            return

        add_to: _Entries = self
        root_typ_file_group = self.root_file_groups.must_protect
        if self.typ is GroupType.MAY_WORK_ON:
            root_typ_file_group = self.root_file_groups.may_work_on
            # Check for match against configured protect patterns, if match, then the file must go to the protect group instead
            if pattern:
                _LOG.debug("'%s' is protected by regex %s. Add to self.other (GroupType.MAY_WORK_ON) instead.", entry.path, pattern)
                add_to = self.other
                root_typ_file_group = self.root_file_groups.must_protect

        if entry.is_symlink():
            # cast: https://github.com/python/mypy/issues/11964
            points_to = os.readlink(cast(str, entry))

            if entry.is_dir(follow_symlinks=True):
                _LOG.debug("%s - '%s' -> '%s' is a symlink to a directory - ignoring", self.typ.name, entry.path, points_to)
                add_to.num_directory_symlinks += 1
                return

            add_to.symlinks[entry.name] = entry

            abs_points_to = os.path.normpath(os.path.join(self.abs_dir_path, points_to))
            root_typ_file_group.symlinks_by_abs_points_to[abs_points_to].append(entry)
            return

        _LOG.debug("%s - %s, entry name: %s, add_to: %s", self.abs_dir_path, self.typ.name, entry.name, "self" if add_to is self else "other")

        # Check if file name matches include/exclude pattern and determine whether to add file to 'files'.
        if not self.include_exclude:
            add_to.files[entry.name] = entry
            return

        if (match := (self.include_exclude.match(entry.name) or self.include_exclude.match(str(self.abs_dir_path/entry.name)))) and self.typ == GroupType.MUST_PROTECT:
            _LOG.debug(" %s - exclude %s, match %s", self.typ, self.include_exclude, match)
            return

        if not match and self.typ == GroupType.MAY_WORK_ON:
            _LOG.debug(" %s - include %s, no match %s", self.typ, self.include_exclude, match)
            return

        add_to.files[entry.name] = entry

    def collect(self) -> None:
        """Recursively find all files and directories belonging to 'group'

        Insert self in global 'dirs' dict.
        """

        _LOG.debug("collect %s: %s", self.typ.name, self.abs_dir_path)

        for entry in os.scandir(self.abs_dir_path):
            self.handle_entry(entry)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(\n" + pformat(self.__dict__, indent=4) + ")"


@dataclass
class _FileGroupsEntries():
    """Provides __contains__ and items()."""
    __slots__ = ('dirs', 'typ', 'prop_name')

    def __init__(self, dirs: dict[str, DirGroups], typ: GroupType, prop_name: str):
        self.dirs = dirs
        self.typ = typ
        self.prop_name = prop_name

    def _files_symlinks(self, dir_grps: DirGroups) -> dict[str, DirEntry]:
        entries: _Entries = dir_grps if dir_grps.typ == self.typ else dir_grps.other
        # _LOG.debug("_files_symlinks: self.typ: %s, dir_grps.typ: %s", self.typ, dir_grps.typ)
        prop_val = getattr(entries, self.prop_name)
        # _LOG.debug("prop_name %s, prop_val %s", self.prop_name, prop_val)
        return cast(dict[str, DirEntry], prop_val)

    def __contains__(self, left: str) -> bool:
        abs_file_path = Path(left)
        dir_grps = self.dirs.get(str(abs_file_path.parent))
        # _LOG.debug("__contains__: abs_file_path: %s, dir_grps %s", abs_file_path, dir_grps)

        if dir_grps and (abs_file_path.name in self._files_symlinks(dir_grps)):
            return True

        return False

    def items(self) -> Iterator[tuple[str, DirEntry]]:
        """Iterate path, DirEntry of self.typ"""
        # _LOG.debug("%s items - %s", self.typ, self.prop_name)
        for abs_dir_path, dir_grps in self.dirs.items():
            for file_name, dir_entry in self._files_symlinks(dir_grps).items():
                yield str(Path(abs_dir_path)/file_name), dir_entry

    def values(self) -> Iterator[DirEntry]:
        """Iterate DirEntry of self.typ"""
        # _LOG.debug("%s values - %s", self.typ, self.prop_name)
        for _, val in self.items():
            yield val

    def __iter__(self) -> Iterator[str]:
        """Iterate path of self.typ"""
        for abs_path, _ in self.items():
            yield abs_path

    keys = __iter__

    def __len__(self) -> int:
        """Number of paths of self.typ"""
        length = 0
        for _, dir_grps in self.dirs.items():
            length += len(self._files_symlinks(dir_grps))

        return length


class _FileGroupHolder():
    __slots__ = ('dirs', 'typ', 'files', 'symlinks', 'symlinks_by_abs_points_to')

    def __init__(self, dirs: dict[str, DirGroups], typ: GroupType):
        self.dirs = dirs
        self.typ = typ
        self.files = _FileGroupsEntries(dirs=dirs, typ=typ, prop_name="files")
        self.symlinks = _FileGroupsEntries(dirs=dirs, typ=typ, prop_name="symlinks")
        self.symlinks_by_abs_points_to: dict[str, list[DirEntry]] = defaultdict(list)

    @property
    def num_directories(self) -> int:
        """Number of directories of self.typ visited."""
        return sum((1 for dd in self.dirs.values() if dd.typ == self.typ))

    @property
    def num_directory_symlinks(self) -> int:
        """Number of directories of self.typ visited."""
        return sum((dd.num_directory_symlinks for dd in self.dirs.values() if dd.typ == self.typ))


class FileGroups():
    """Create six different groups of regular files and symlinks by collecting files under specified directories.

    Note that directory symlinks are followed for the specified arguments!, but never for any subdirectories.

    Config Files
    See `config.file_loader` for description of config file format and arguments.

    Arguments:
        protect_dirs_seq: Directories in which (regular) files may not be deleted/modified.
            Directory may be a subdirectory of (or the same, for convenient globbing) as a work_dirs_seq directory.

        work_dirs_seq: Directories in which to potentially delete/rename/modify files.
            Directory may be a subdirectory of (or the same, for convenient globbing) as a protect_dirs_seq directory.

        protect_exclude: Exclude files matching regex in the protected files (does not apply to symlinks). Default: Include ALL.
            Note: Since these files are excluded from protection, it means they er NOT protected!
        work_include: ONLY include files matching regex in the may_work_on files (does not apply to symlinks). Default: Include ALL.

        config_handler: Load config files. See config.config_handler.ConfigHandler and config.file_loader.ConfigFileLoader.
            Note that the default 'None' means use the `config.config_handler.ConfigHandler` class with default arguments.
    """

    def __init__(
            self,
            protect_dirs_seq: Sequence[Path], work_dirs_seq: Sequence[Path],
            *,
            protect_exclude: re.Pattern|None = None, work_include: re.Pattern|None = None,
            config_handler: ConfigHandler|None = None,
            path_display: PathDisplay|None = None) -> None:
        super().__init__()
        self.protect_exclude = protect_exclude
        self.work_include = work_include
        self.config_handler = config_handler or ConfigHandler(path_display=path_display or PathDisplay())
        self.dir_config = self.config_handler.load_config_dir_files()
        self.abs_dir_path = Path(".").resolve()  # Dir args are relative to current dir.
        self.dirs: dict[str, DirGroups] = {}

        self.must_protect = _FileGroupHolder(self.dirs, GroupType.MUST_PROTECT)
        self.may_work_on = _FileGroupHolder(self.dirs, GroupType.MAY_WORK_ON)

        # Turn all directory paths into absolute paths with symlinks resolved, keep referrence to original argument for messages
        # Sort the input by length to guarantee that parents are handled first
        protect_dirs: dict[str, tuple[GroupType, Path]] = {str(Path(pd).resolve()): (GroupType.MUST_PROTECT, pd) for pd in protect_dirs_seq}
        work_dirs: dict[str, tuple[GroupType, Path]] = {str(Path(wd).resolve()): (GroupType.MAY_WORK_ON, wd) for wd in work_dirs_seq}

        for any_dir, (group_type, input_path) in sorted(chain(protect_dirs.items(), work_dirs.items()), key=lambda item: len(Path(item[0]).parts)):
            if group_type == GroupType.MAY_WORK_ON and any_dir in protect_dirs:
                input_protect_dir = protect_dirs[any_dir][1]

                if input_path == input_protect_dir:
                    _LOG.info("Ignoring 'work' dir '%s' which is also a 'protect' dir.", input_path)
                    continue

                _LOG.info("Ignoring 'work' dir '%s' (from argument '%s') which is also a 'protect' dir (from argument '%s').", any_dir, input_path, input_protect_dir)
                continue

            parent = self.dirs.get(str(Path(any_dir).parent)) or self
            dg = DirGroups(group_type, self, Path(any_dir), parent)
            self.dirs[any_dir] = dg

        for _, dg in list(self.dirs.items()):
            dg.collect()

    def dump(self) -> None:
        """Log collected files. This may be A LOT of output for large directories."""

        log = _LOG.getChild("dump")
        lvl = logging.DEBUG
        if not log.isEnabledFor(lvl):
            return

        log.log(lvl, "")

        log.log(lvl, "must protect:")
        for path in self.must_protect.files:
            log.log(lvl, "%s", path)
        log.log(lvl, "")

        log.log(lvl, "must protect symlinks:")
        for path in self.must_protect.symlinks:
            log.log(lvl, "%s -> %s", path, os.readlink(path))
        log.log(lvl, "")

        log.log(lvl, "must protect symlinks by absolute points to:")
        for abs_points_to, lnks in self.must_protect.symlinks_by_abs_points_to.items():
            log.log(lvl, "%s -> %s", lnks, abs_points_to)
        log.log(lvl, "")

        log.log(lvl, "may work on:")
        for path in self.may_work_on.files:
            log.log(lvl, "%s", path)
        log.log(lvl, "")

        log.log(lvl, "may work on symlinks:")
        for path in self.may_work_on.symlinks:
            log.log(lvl, "%s -> %s", path, os.readlink(path))
        log.log(lvl, "")

        log.log(lvl, "may work on symlinks by absolute points to:")
        for abs_points_to, lnks in self.may_work_on.symlinks_by_abs_points_to.items():
            log.log(lvl, "%s -> %s", lnks, abs_points_to)
        log.log(lvl, "")

        log.log(lvl, "")

    def stats(self) -> None:
        """Log collection numbers."""
        log = _LOG.getChild("stats")
        lvl = logging.INFO
        if not log.isEnabledFor(lvl):
            return

        log.log(lvl, "collected protect_directories: %s", self.must_protect.num_directories)
        log.log(lvl, "collected protect_directory_symlinks: %s", self.must_protect.num_directory_symlinks)
        log.log(lvl, "collected work_on_directories: %s", self.may_work_on.num_directories)
        log.log(lvl, "collected work_on_directory_symlinks: %s", self.may_work_on.num_directory_symlinks)

        log.log(lvl, "collected must_protect_files: %s", len(self.must_protect.files))
        log.log(lvl, "collected must_protect_symlinks: %s", len(self.must_protect.symlinks))
        log.log(lvl, "collected may_work_on_files: %s", len(self.may_work_on.files))
        log.log(lvl, "collected may_work_on_symlinks: %s", len(self.may_work_on.symlinks))
