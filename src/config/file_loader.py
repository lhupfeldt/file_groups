import ast
import re
from pathlib import Path
from pprint import pformat
import logging
from typing import Any

from .dir_config import RecursiveConfig, DirConfig


_LOG = logging.getLogger(__name__)


_NO_CFG: tuple[dict[str, Any], None] = ({
    "local": set(),
    "recursive": set(),
}, None)


class ConfigException(Exception):
    """Invalid configuration"""


class ConfigFileLoader():
    r"""Handle config file loadinf. Also See `ConfigHandler` for more info.

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
        app_dirs: Provide your own instance of AppDirs in addition to or as a replacement of the default to add config file names and path.
            Configuration from later entries have higher precedence.
            Note that if no AppDirs are specified, no config files will be loaded, neither from config dirs, nor from collected directories.
            See: https://pypi.org/project/appdirs/

    Members:
       conf_file_names: File names which are config files.
    """

    _fg_key = "file_groups"
    _protect_key = "protect"
    _valid_dir_protect_scopes = ("local", "recursive")

    def __init__(self, conf_file_name_pairs: tuple[tuple[str, str], ...], ignore_per_directory_config_files: bool =False):
        super().__init__()

        self.conf_file_name_pairs = conf_file_name_pairs
        self.ignore_per_directory_config_files = ignore_per_directory_config_files

        # self.default_config_file_example = self.default_config_file.with_suffix('.example.py')

    def _read_and_eval_config_file_for_conf_file_pair(
            self, conf_dir: Path, conf_file_name_pair: tuple[str, str], ignore_config_files: bool
    ) -> tuple[dict[str, Any], Path|None]:
        """Read config file.

        Error if config files are found both with and withput '.' prefix.
        Return: (Config dict, config file name) if no config file is found return _NO_CFG.
        """

        assert conf_dir.is_absolute()
        _LOG.debug("Checking for config files %s in directory: %s", conf_file_name_pair, conf_dir)

        match [conf_dir/cf_name for cf_name in conf_file_name_pair if cf_name and (conf_dir/cf_name).exists()]:
            case []:
                _LOG.debug("No config file in directory %s", conf_dir)
                return _NO_CFG

            case [conf_file]:
                if ignore_config_files:
                    _LOG.debug("Ignoring config file: %s", conf_file)
                    return _NO_CFG

                _LOG.debug("Read config file: %s", conf_file)
                with open(conf_file, encoding="utf-8") as fh:
                    new_config = ast.literal_eval(fh.read())
                _LOG.debug("%s", pformat(new_config))
                return new_config, conf_file

            case config_files:
                msg = f"More than one config file in dir '{conf_dir}': {[cf.name for cf in config_files]}."
                _LOG.debug("%s", msg)
                raise ConfigException(msg)

    def read_and_validate_config_file_for_conf_file_pair(
            self, conf_dir: Path, conf_file_name_pair: tuple[str, str], valid_protect_scopes: tuple[str, ...], ignore_config_files: bool
    ) -> tuple[dict[str, set[re.Pattern]], Path|None]:
        """Read config file, validate keys and compile regexes.

        Error if config files are found both with and withput '.' prefix.

        Return: merged config dict with compiled regexes, config file name. If no config files is found, then return empty sets and None.
        """

        new_config, conf_file = self._read_and_eval_config_file_for_conf_file_pair(conf_dir, conf_file_name_pair, ignore_config_files)
        if not conf_file:
            return _NO_CFG

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

    def dir_config(self, conf_dir: Path, parent_conf: RecursiveConfig) -> DirConfig:
        """Read and merge config file from directory 'conf_dir' with 'parent_conf'.

        If directory has no parent in the file_groups included dirs, then the global conf must be passed as parent.
        """

        cfg_merge_local: set[re.Pattern] = set()
        cfg_merge_recursive: set[re.Pattern] = set()
        cfg_files: list[str] = []

        for conf_file_name_pair in self.conf_file_name_pairs:
            cfg, cfg_file = self.read_and_validate_config_file_for_conf_file_pair(
                conf_dir, conf_file_name_pair, self._valid_dir_protect_scopes, self.ignore_per_directory_config_files)
            cfg_merge_recursive.update(cfg.get("recursive", set()))
            cfg_merge_local.update(cfg.get("local", set()))
            if cfg_file:
                cfg_files.append(cfg_file.name)

        new_config = DirConfig(cfg_merge_recursive | parent_conf.protect_recursive, cfg_merge_local, conf_dir, cfg_files)
        _LOG.debug("new_config:\n %s", new_config)

        return new_config
