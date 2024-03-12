import ast
import os
import errno
import re
from pathlib import Path
import itertools
from pprint import pformat
import logging
from dataclasses import dataclass
from typing import Tuple, Sequence, Any

from appdirs import AppDirs # type: ignore

from .types import FsPath


_LOG = logging.getLogger(__name__)


class ConfigException(Exception):
    """Invalid configuration"""


@dataclass
class ProtectConfig():
    """Hold global (site or user) protect config."""
    protect_recursive: set[re.Pattern]

    def __json__(self):
        return {
            ProtectConfig.__name__: {
                "protect_recursive": [str(pat) for pat in self.protect_recursive],
            }
        }


@dataclass
class DirConfig(ProtectConfig):
    """Hold directory specific protect config."""
    protect_local: set[re.Pattern]
    config_dir: Path|None
    config_files: list[str]

    def is_protected(self, ff: FsPath):
        """If ff id protected by a regex pattern then return the pattern, otherwise return None."""

        # _LOG.debug("ff '%s'", ff)
        for pattern in itertools.chain(self.protect_local, self.protect_recursive):
            if os.sep in str(pattern):
                # _LOG.debug("Pattern '%s' has path sep", pattern)
                assert os.path.isabs(ff), f"Expected absolute path, got '{ff}'"

                # Search against full path
                if pattern.search(os.fspath(ff)):
                    return pattern

                # Attempt exact match against path relative to , i.e. if pattern starts with '^'.
                # This makes sense for patterns specified on commandline
                cwd = os.getcwd()
                ff_relative = str(Path(ff).relative_to(cwd))
                # _LOG.debug("ff '%s' relative to start dir'%s'", ff_relative, cwd)

                if pattern.match(ff_relative):
                    return pattern

            elif pattern.search(ff.name):
                return pattern

        return None

    def __json__(self):
        return {
            DirConfig.__name__: super().__json__()[ProtectConfig.__name__] | {
                "protect_local": [str(pat) for pat in self.protect_local],
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
        remember_configs: Store loaded and merged configs in `per_dir_configs` member variable.
        app_dirs: Provide your own instance of AppDirs in addition to or as a replacement of the default to add config file names and path.
            Configuration from later entries have higher precedence.
            Note that if no AppDirs are specified, no config files will be loaded, neither from config dirs, nor from collected directories.
            See: https://pypi.org/project/appdirs/

    Members:
       conf_file_names: File names which are config files.
       remember_configs: Whether per directory resolved/merged configs are stored in `per_dir_configs`.
       per_dir_configs: Mapping from dir name to directory specific config dict. Only if remember_configs is True.
    """

    default_appdirs: AppDirs = AppDirs("file_groups", "Hupfeldt_IT")

    _fg_key = "file_groups"
    _protect_key = "protect"
    _valid_dir_protect_scopes = ("local", "recursive")
    _valid_config_dir_protect_scopes = ("local", "recursive", "global")

    def __init__(
            self, protect: Sequence[re.Pattern] = (),
            ignore_config_dirs_config_files=False, ignore_per_directory_config_files=False, remember_configs=True,
            app_dirs: Sequence[AppDirs]|None = None,
            *,
            config_file: Path|None = None,
        ):
        super().__init__()

        self._global_config = ProtectConfig(set(protect))
        self.remember_configs = remember_configs
        self.per_dir_configs: dict[Path, DirConfig] = {}  # key is abs_dir_path
        self.ignore_per_directory_config_files = ignore_per_directory_config_files

        app_dirs = app_dirs or (ConfigFiles.default_appdirs,)
        self.conf_file_name_pairs = tuple((apd.appname + ".conf", "." + apd.appname + ".conf") for apd in app_dirs)
        _LOG.debug("Conf file names: %s", self.conf_file_name_pairs)
        self.conf_file_names = list(itertools.chain.from_iterable(self.conf_file_name_pairs))

        self.ignore_config_dirs_config_files = ignore_config_dirs_config_files
        self.config_dirs = []
        for appd in app_dirs:
            self.config_dirs.extend(appd.site_config_dir.split(':'))
        for appd in app_dirs:
            self.config_dirs.append(appd.user_config_dir)

        self.config_file = config_file

        # self.default_config_file_example = self.default_config_file.with_suffix('.example.py')

    def _read_and_eval_config_file_for_one_appname(
            self, conf_dir: Path, conf_file_name_pair: Sequence[str], ignore_config_files: bool
    ) -> Tuple[dict[str, Any], Path|None]:
        """Read config file.

        Error if config files are found both with and withput '.' prefix.
        Return: Config dict, config file name, or if no config files is found, None, None.
        """

        assert conf_dir.is_absolute()
        _LOG.debug("Checking for config files %s in directory: %s", conf_file_name_pair, conf_dir)

        match [conf_dir/cfn for cfn in conf_file_name_pair if (conf_dir/cfn).exists()]:
            case []:
                _LOG.debug("No config file in directory %s", conf_dir)
                return {}, None

            case [conf_file]:
                if ignore_config_files:
                    _LOG.debug("Ignoring config file: %s", conf_file)
                    return {}, None

                _LOG.debug("Read config file: %s", conf_file)
                with open(conf_file, encoding="utf-8") as fh:
                    new_config = ast.literal_eval(fh.read())
                _LOG.debug("%s", pformat(new_config))
                return new_config, conf_file

            case config_files:
                msg = f"More than one config file in dir '{conf_dir}': {[cf.name for cf in config_files]}."
                _LOG.debug("%s", msg)
                raise ConfigException(msg)

    def _read_and_validate_config_file_for_one_appname(
            self, conf_dir: Path, conf_file_name_pair: Sequence[str], valid_protect_scopes: Tuple[str, ...], ignore_config_files: bool
    ) -> Tuple[dict[str, set[re.Pattern]], Path|None]:
        """Read config file, validate keys and compile regexes.

        Error if config files are found both with and withput '.' prefix.

        Return: merged config dict with compiled regexes, config file name. If no config files is found, then return empty sets and None.
        """

        new_config, conf_file = self._read_and_eval_config_file_for_one_appname(conf_dir, conf_file_name_pair, ignore_config_files)
        if not new_config:
            return {
                "local": set(),
                "recursive": set(),
            }, None

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

        for key in self._valid_dir_protect_scopes:  # Do NOT use the 'valid_protect_scopes' argument here
            protect_conf.setdefault(key, set())

        lvl = logging.DEBUG
        if _LOG.isEnabledFor(lvl):
            _LOG.log(lvl, "Merged directory config:\n%s", pformat(new_config))

        return protect_conf, conf_file

    def load_config_dir_files(self) -> None:
        """Load config files from platform standard directories and specified config file, if any."""

        if not self.ignore_config_dirs_config_files:
            _LOG.debug("config_dirs: %s", self.config_dirs)
            for conf_dir in self.config_dirs:
                conf_dir = Path(conf_dir)
                if not conf_dir.exists():
                    continue

                for conf_file_name_pair in self.conf_file_name_pairs:
                    cfg, _ = self._read_and_validate_config_file_for_one_appname(
                        conf_dir, conf_file_name_pair, self._valid_config_dir_protect_scopes, self.ignore_config_dirs_config_files)
                    self._global_config.protect_recursive |= cfg.get("global", set())

        if self.config_file:
            _LOG.debug("specified config_file: %s", self.config_file)
            conf_dir = self.config_file.parent.absolute()
            conf_name = self.config_file.name
            cfg, fpath = self._read_and_validate_config_file_for_one_appname(
                conf_dir, (conf_name,), self._valid_config_dir_protect_scopes, self.ignore_config_dirs_config_files)
            if not fpath:
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(self.config_file))
            self._global_config.protect_recursive |= cfg.get("global", set())

        _LOG.debug("Merged global config:\n %s", self._global_config)

    def dir_config(self, conf_dir: Path, parent_conf: DirConfig|None) -> DirConfig:
        """Read and merge config file from directory 'conf_dir' with 'parent_conf'.

        If directory has no parent in the file_groups included dirs, then None should be supplied as parent_conf.
        """

        cfg_merge_local: set[re.Pattern] = set()
        cfg_merge_recursive: set[re.Pattern] = set()
        cfg_files: list[str] = []

        for conf_file_name_pair in self.conf_file_name_pairs:
            cfg, cfg_file = self._read_and_validate_config_file_for_one_appname(
                conf_dir, conf_file_name_pair, self._valid_dir_protect_scopes, self.ignore_per_directory_config_files)
            cfg_merge_local.update(cfg.get("local", set()))
            cfg_merge_recursive.update(cfg.get("recursive", set()))
            if cfg_file:
                cfg_files.append(cfg_file.name)

        parent_protect_recursive = parent_conf.protect_recursive if parent_conf else self._global_config.protect_recursive
        new_config = DirConfig(cfg_merge_recursive | parent_protect_recursive, cfg_merge_local, conf_dir, cfg_files)
        _LOG.debug("new_config:\n %s", new_config)

        if self.remember_configs:
            self.per_dir_configs[conf_dir] = new_config
            # _LOG.debug("per_dir_configs:\n %s", self.per_dir_configs)

        return new_config
