import ast
import os
import re
from pathlib import Path
import itertools
from pprint import pformat
import logging
from dataclasses import dataclass
from typing import Tuple, Sequence

from appdirs import AppDirs # type: ignore

from .types import FsPath


_LOG = logging.getLogger(__name__)


class ConfigException(Exception):
    """Invalid configuration"""


@dataclass
class DirConfig():
    """Hold protect config for a directory, or global (site or user) config."""
    protect: dict[str, set[re.Pattern]]
    config_dir: Path|None
    config_files: Sequence[str]

    def is_protected(self, ff: FsPath):
        """If ff id protected by a regex pattern then return the pattern, otherwise return None."""

        for pattern in itertools.chain(self.protect["local"], self.protect["recursive"]):
            if os.sep in str(pattern):
                # Match against full path
                assert os.path.isabs(ff), f"Expected absolute path, got '{ff}'"
                if pattern.search(os.fspath(ff)):
                    return pattern

            elif pattern.search(ff.name):
                return pattern

        return None

    def __json__(self):
        return {
            "DirConfig": {
                "protect": {key: list(str(pat) for pat in val) for key, val in self.protect.items()},
                "config_dir": str(self.config_dir),
                "config_files": self.config_files,
            }
        }


class ConfigFiles():
    r"""Handle config files.

    Config files are searched for in the standard config directories on the platform AND in any collected directory.

    The 'app_dirs' default sets default config dirs and config-file names.
    It is also possible to specify additional or alternative config files specific to the application using this library.
    Config files must be named after the AppDirs.appname (first argument) as <appname>.conf or .<appname>.conf.
    The defaults are 'file_groups.conf' and '.file_groups.conf'.
    You should consider carefully before disabling loading of the default files, as an end user likely wants the protection rules to apply for any
    application using this library.

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

    The level one key is 'file_groups'.
    Applications are free to add entries at this level, but not underneath. This is protect against ignored misspelled keys.

    The 'file_groups' entry is a dict with a single 'protect' entry.
    The 'protect' entry is a dict with at most three entries: 'local', 'recursive' and 'global'. These specify whether a directory specific
    configuration will inherit and extend the parent (and global) config, or whether it is local to current directory only.
    The 'local', 'recursive' and 'global' entries are lists of regex patterns to match against collected 'work_on' files.
    Regexes are checked against the simple file name (i.e. not the full path) unless they contain at least one path separator (os.sep), in
    which case they are checked against the absolute path.
    All checks are done as regex *search* (better to protect too much than too little). Write the regex to match the full name or path if needed.

    Note that for security ast.literal_eval is used to interpret the config, so no code is allowed.

    Arguments:
        protect: An optional sequence of regexes to be added to protect[recursive] for all directories.
        ignore_config_dirs_config_files: Ignore config files in standard config directories.
        ignore_per_directory_config_files: Ignore config files in collected directories.
        remember_configs: Store loaded and merged configs in `dir_configs` member variable.
        app_dirs: Provide your own instance of AppDirs in addition to or as a replacement of the default to add config file names and path.
            Configuration from later entries have higher precedence.
            Note that if no AppDirs are specified, no config files will be loaded, neither from config dirs, nor from collected directories.
            See: https://pypi.org/project/appdirs/

    Members:
       remember_configs: Whether per directory resolved/merged configs are stored in `dir_configs`.
       dir_configs: dict[str: dict] Mapping from dir name to directory specific config dict. Only if remember_configs is True.
    """

    default_appdirs: AppDirs = AppDirs("file_groups", "Hupfeldt_IT")

    _fg_key = "file_groups"
    _protect_key = "protect"
    _valid_dir_protect_scopes = ("local", "recursive")
    _valid_config_dir_protect_scopes = ("local", "recursive", "global")

    def __init__(
            self, protect: Sequence[re.Pattern] = (),
            ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, remember_configs=False,
            app_dirs: Sequence[AppDirs]|None = None):
        super().__init__()

        self._global_config = DirConfig({
            "local": set(),
            "recursive": set(protect),
        }, None, ())

        self.remember_configs = remember_configs
        self.per_dir_configs: dict[str, DirConfig] = {}  # key is abs_dir_path
        self.ignore_per_directory_config_files = ignore_per_directory_config_files

        app_dirs = app_dirs or (ConfigFiles.default_appdirs,)
        self.conf_file_names = tuple((apd.appname + ".conf", "." + apd.appname + ".conf") for apd in app_dirs)
        _LOG.debug("Conf file names: %s", self.conf_file_names)
        if not ignore_config_dirs_config_files:
            config_dirs = []
            for appd in app_dirs:
                config_dirs.extend(appd.site_config_dir.split(':'))
            for appd in app_dirs:
                config_dirs.append(appd.user_config_dir)
            self._load_config_dir_files(config_dirs)

    # self.default_config_file_example = self.default_config_file.with_suffix('.example.py')

    def _read_and_validate_config_file_for_one_appname(  # pylint: disable=too-many-locals
            self, conf_dir: Path, conf_file_name_pair: Sequence[str], parent_conf: DirConfig, valid_protect_scopes: Tuple[str, ...], ignore_config_files: bool
    ) -> Tuple[dict[str, set[re.Pattern]], str|None]:
        """Read config file, validate keys and compile regexes and merge with parent.

        Error if config files are found both with and withput '.' prefix.
        Merge parent conf into conf_dir conf (if any) and return the merged dict. The parent conf is not modified.

        Return: merged config dict with compiled regexes, config file name. If no config files is found, then return inherited parent conf and None.
        """

        assert conf_dir.is_absolute()
        _LOG.debug("Checking for config files %s in directory: %s", conf_file_name_pair, conf_dir)

        match [conf_dir/cfn for cfn in conf_file_name_pair if (conf_dir/cfn).exists()]:
            case []:
                _LOG.debug("No config file in directory %s", conf_dir)
                no_conf_file: dict[str, set[re.Pattern]] = {
                    "local": set(),
                    "recursive": parent_conf.protect["recursive"]
                }
                return no_conf_file, None

            case [conf_file]:
                if ignore_config_files:
                    _LOG.debug("Ignoring config file: %s", conf_file)
                    return self._global_config.protect, None

                _LOG.debug("Read config file: %s", conf_file)
                with open(conf_file, encoding="utf-8") as fh:
                    new_config = ast.literal_eval(fh.read())
                _LOG.debug("%s", pformat(new_config))

            case config_files:
                msg = f"More than one config file in dir '{conf_dir}': {[cf.name for cf in config_files]}."
                _LOG.debug("%s", msg)
                raise ConfigException(msg)

        try:
            protect_conf: dict[str, set[re.Pattern]] = new_config[self._fg_key][self._protect_key]
        except KeyError as ex:
            raise ConfigException(f"Config file '{conf_file}' is missing mandatory configuration '{self._fg_key}[{self._protect_key}]'.") from ex

        for key, val in protect_conf.items():
            if key not in valid_protect_scopes:
                msg = f"The only keys allowed in '{self._fg_key}[{self._protect_key}]' section in the config file '{conf_file}' are: {valid_protect_scopes}. Got: '{key}'."
                _LOG.debug("%s", msg)
                raise ConfigException(msg)

            protect_conf[key] = set(re.compile(pattern) for pattern in val)
            if key == "recursive":
                protect_conf[key].update(parent_conf.protect[key])

        for key in self._valid_dir_protect_scopes:  # Do NOT use the 'valid_protect_scopes' argument here
            protect_conf.setdefault(key, set())

        lvl = logging.DEBUG
        if _LOG.isEnabledFor(lvl):
            _LOG.log(lvl, "Merged directory config:\n%s", pformat(new_config))

        return protect_conf, conf_file.name

    def _read_and_validate_config_files(
            self, conf_dir: Path, parent_conf: DirConfig, valid_protect_scopes: Tuple[str, ...], ignore_config_files: bool) -> DirConfig:
        cfg_merge: dict[str, set[re.Pattern]] = {}
        cfg_files: list[str] = []
        for conf_file_name_pair in self.conf_file_names:
            cfg, cfg_file = self._read_and_validate_config_file_for_one_appname(
                conf_dir, conf_file_name_pair, parent_conf, valid_protect_scopes, ignore_config_files)
            for key, val in cfg.items():
                cfg_merge.setdefault(key, set()).update(val)
            if cfg_file:
                cfg_files.append(cfg_file)

        return DirConfig(cfg_merge, conf_dir, cfg_files)

    def _load_config_dir_files(self, config_dirs):
        _LOG.debug("config_dirs: %s", config_dirs)
        for conf_dir in config_dirs:
            conf_dir = Path(conf_dir)
            if not conf_dir.exists():
                continue

            new_config = self._read_and_validate_config_files(conf_dir, self._global_config, self._valid_config_dir_protect_scopes, False)
            if self.remember_configs:
                self.per_dir_configs[str(conf_dir)] = new_config

            self._global_config.protect["recursive"].update(new_config.protect.get("global", set()))
            _LOG.debug("Merged global config:\n %s", new_config)

            try:
                del new_config.protect['global']
            except KeyError:
                pass

    def dir_config(self, conf_dir: Path, parent_conf: DirConfig|None) -> DirConfig:
        """Read and merge config file from directory 'conf_dir' with 'parent_conf'.

        If directory has no parent in the file_groups included dirs, then None should be supplied as parent_conf.
        """

        new_config = self._read_and_validate_config_files(
            conf_dir, parent_conf or self._global_config, self._valid_dir_protect_scopes, self.ignore_per_directory_config_files)
        _LOG.debug("new_config:\n %s", new_config)

        if self.remember_configs:
            self.per_dir_configs[str(conf_dir)] = new_config
            # _LOG.debug("per_dir_configs:\n %s", self.per_dir_configs)

        return new_config
