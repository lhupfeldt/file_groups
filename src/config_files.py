from __future__ import annotations

import ast
import os
import re
from pathlib import Path
import itertools
from pprint import pformat
import logging
from typing import Mapping, Tuple, Sequence, cast

from appdirs import AppDirs # type: ignore

from .types import FsPath


_LOG = logging.getLogger(__name__)


class ConfigException(Exception):
    """Invalid configuration"""


class ConfigFiles():
    r"""Handle config files.

    Config files are searched for in the standard config directories on the platform AND in any collected directory.
    Config files in config directories must be named 'file_groups.conf' and in collected directories '.file_groups.conf' or 'file_groups.conf'.

    The content of a conf file is a Python dict with the following structure.

        {
            "file_groups": {  # Required
                "protect": {  # Optional
                    "local": [  # Optional
                        ...  # Regex patterns
                    ],
                    "recursive": [  # Optional, merged with parent config dir property
                        ... # Regex patterns
                    ]
                    "global": [  # Optional. Only allowed in config directory files. Merged into collect dir configs 'recursive' property.
                        ...  # Regex patterns
                    ],
                },
            }
            ...
        }

    E.g.:

        {
            "file_groups": {
                "protect": {
                    "recursive": [
                        r"PP.*\.jpg",  # Don't mess with JPEG files starting with 'PP'.
                    ]
                }
            }
        }

    The level one keys (e.g. 'file_groups') are the application (library) names.
    Applications are free to add entries at this level.

    The 'file_groups' entry is a dict with a single 'protect' entry.
    The 'protect' entry is a dict with at most three entries: 'local', 'recursive' and 'global'. These specify whether a directory specific
    configuration will inherit and extend the parent (and global) config, or whether it is local to current directory only.
    The 'local', 'recursive' and 'global' entries are lists of regex patterns to match against collected 'work_on' files.
    Regexes are checked against the simple filename (i.e. not the full path) unless they contain at least one path separator (os.sep), in
    which case they are checked against the absolute path.
    All checks are done as regex *search* (better to protect too much than too little). Write the regex to match the full name or path if needed.

    Note that for security ast.literal_eval is used to interpret the config, so no code is allowed.

    Arguments:
        protect: An optional sequence of regexes to be added to protect[recursive] for all directories.
        ignore_config_dirs_config_files: Ignore config files in standard config directories.
        ignore_per_directory_config_files: Ignore config files in collected directories.
        remember_configs: Store loaded and merged configs in `dir_configs` member variable.

    Members:
       global_config: dict
       remember_configs: Whether per directory resolved/merged configs are stored in `dir_configs`.
       dir_configs: dict[str: dict] Mapping from dir name to directory specific config dict. Only if remember_configs is True.
    """

    _conf_file_names = [".file_groups.conf", "file_groups.conf"]
    _fg_key = "file_groups"
    _protect_key = "protect"
    _valid_dir_protect_scopes = ("local", "recursive")
    _valid_config_dir_protect_scopes = ("local", "recursive", "global")

    def __init__(
            self, protect: Sequence[re.Pattern] = (),
            ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, remember_configs=False):
        super().__init__()
        self.remember_configs = remember_configs

        self.per_dir_configs: dict[str, dict] = {}  # key is abs_dir_path, value is config dict
        self.global_config = {
            "file_groups": {
                "protect": {
                    "local": set(),
                    "recursive": set(protect),
                }
            }
        }

        self.ignore_per_directory_config_files = ignore_per_directory_config_files

        if not ignore_config_dirs_config_files:
            app_dirs = AppDirs("file_groups", "Hupfeldt_IT")
            config_dirs = app_dirs.site_config_dir.split(':') + [app_dirs.user_config_dir]
            _LOG.debug("config_dirs: %s", config_dirs)
            gfpt = self.global_config["file_groups"]["protect"]
            for conf_dir in config_dirs:
                conf_dir = Path(conf_dir)
                if not conf_dir.exists():
                    continue

                new_config, _ = self._read_and_validate_config_file(conf_dir, self.global_config, self._valid_config_dir_protect_scopes, False)
                if self.remember_configs:
                    self.per_dir_configs[str(conf_dir)] = new_config

                fpt = new_config["file_groups"]["protect"]
                cast(set, gfpt["recursive"]).update(fpt.get("global", ()))
                _LOG.debug("Merged global config:\n %s", pformat(new_config))

                try:
                    del fpt['global']
                except KeyError:
                    pass

        # self.default_config_file_example = self.default_config_file.with_suffix('.example.py')

    def _get_single_conf_file(self, conf_dir: Path, ignore_config_files: bool) -> Tuple[dict|None, Path|None]:
        """Return the config file content and path if any config file is found in conf_dir. Error if two are found."""
        _LOG.debug("Checking for config file in directory: %s", conf_dir)

        num_files = 0
        for cfn in self._conf_file_names:
            tmp_conf_file = conf_dir/cfn
            if tmp_conf_file.exists():
                conf_file = tmp_conf_file
                num_files += 1

        if num_files == 1:
            if ignore_config_files:
                _LOG.debug("Ignoring config file: %s", conf_file)
                return None, None

            _LOG.debug("Read config file: %s", conf_file)
            with open(conf_file, encoding="utf-8") as fh:
                new_config = ast.literal_eval(fh.read())
            _LOG.debug("%s", pformat(new_config))
            return new_config, conf_file

        if num_files == 0:
            _LOG.debug("No config file in directory %s", conf_dir)
            return None, None

        msg = f"More than one config file in dir '{conf_dir}': {self._conf_file_names}."
        _LOG.debug("%s", msg)
        raise ConfigException(msg)

    def _read_and_validate_config_file(
            self, conf_dir: Path, parent_conf: dict, valid_protect_scopes: Tuple[str, ...], ignore_config_files: bool
    ) -> Tuple[dict, Path|None]:
        """Read config file, validate keys and compile regexes and merge with parent.

        Merge parent conf into conf_dir conf (if any) and return the merged dict. The parent conf is not modified.

        Return: merged config dict with compiled regexes.
        """

        assert conf_dir.is_absolute()

        no_conf_file = {
            "file_groups": {
                "protect": {
                    "local": set(),
                    "recursive": parent_conf[self._fg_key][self._protect_key]["recursive"]
                }
            }
        }

        new_config, conf_file = self._get_single_conf_file(conf_dir, ignore_config_files)
        if not new_config or ignore_config_files:
            return no_conf_file, None

        try:
            protect_conf = new_config[self._fg_key][self._protect_key]
        except KeyError as ex:
            raise ConfigException(f"Config file '{conf_file}' is missing mandatory configuration '{self._fg_key}[{self._protect_key}]'.") from ex

        for key, val in protect_conf.items():
            if key not in valid_protect_scopes:
                msg = f"The only keys allowed in '{self._fg_key}[{self._protect_key}]' section in the config file '{conf_file}' are: {valid_protect_scopes}. Got: '{key}'."
                _LOG.debug("%s", msg)
                raise ConfigException(msg)

            protect_conf[key] = set(re.compile(pattern) for pattern in val)
            if key == "recursive":
                protect_conf[key].update(parent_conf[self._fg_key][self._protect_key][key])

        for key in self._valid_dir_protect_scopes:  # Do NOT use the 'valid_protect_scopes' argument here
            protect_conf.setdefault(key, set())

        lvl = logging.DEBUG
        if _LOG.isEnabledFor(lvl):
            _LOG.log(lvl, "Merged directory config:\n%s", pformat(new_config))

        return new_config, conf_file

    def dir_config(self, conf_dir: Path, parent_conf: dict) -> Tuple[dict, Path|None]:
        """Read and merge config file from directory 'conf_dir' with 'parent_conf'.

        If directory has no parent in the file_groups included dirs, then self.global_config must be supplied as parent_conf.
        """

        new_config, conf_file = self._read_and_validate_config_file(
            conf_dir, parent_conf, self._valid_dir_protect_scopes, self.ignore_per_directory_config_files)
        if self.remember_configs:
            self.per_dir_configs[str(conf_dir)] = new_config
        return new_config, conf_file

    def is_protected(self, ff: FsPath, dir_config: Mapping):
        """If ff id protected by a regex patterm then return the pattern, otherwise return None."""

        cfg_protected = dir_config[self._fg_key][self._protect_key]
        for pattern in itertools.chain(cfg_protected["local"], cfg_protected["recursive"]):
            if os.sep in str(pattern):
                # Match against full path
                assert os.path.isabs(ff), f"Expected absolute path, got '{ff}'"
                if pattern.search(os.fspath(ff)):
                    return pattern

            elif pattern.search(ff.name):
                return pattern

        return None
