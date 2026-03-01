import os
import errno
import re
from pathlib import Path
import itertools
import logging
from typing import Sequence

from appdirs import AppDirs # type: ignore

from .dir_config import DirConfig
from .file_loader import ConfigFileLoader


_LOG = logging.getLogger(__name__)


class ConfigHandler():
    r"""Handle config files and file protection options.

    Config files are searched for in the standard config directories on the platform AND can be loaded from any collected directory.

    The 'app_dirs' default sets default config dirs and config-file names.
    It is also possible to specify additional or alternative config files specific to the application using this library.
    Config files must be named after the AppDirs.appname (first argument) as <appname>.conf or .<appname>.conf.
    The defaults are 'file_groups.conf' and '.file_groups.conf'.
    You should consider carefully before disabling loading of the default files, as an end user likely wants the protection rules to apply for any
    application using this library.

    See `ConfigFileLoader` for config file format.

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

    default_appdirs: AppDirs = AppDirs("file_groups", "Hupfeldt_IT")
    _valid_config_dir_protect_scopes = ("local", "recursive", "global")

    def __init__(  # pylint: disable=too-many-positional-arguments,too-many-arguments
            self, protect: Sequence[re.Pattern] = (),
            ignore_config_dirs_config_files: bool = False, ignore_per_directory_config_files: bool =False,
            app_dirs: Sequence[AppDirs]|None = None,
            *,
            config_file: Path|None = None,
        ):
        super().__init__()

        self.global_config = DirConfig(set(protect), set(), None, [])
        self.ignore_per_directory_config_files = ignore_per_directory_config_files

        app_dirs = app_dirs or (ConfigHandler.default_appdirs,)
        self.conf_file_name_pairs = tuple((apd.appname + ".conf", "." + apd.appname + ".conf") for apd in app_dirs)
        _LOG.debug("Conf file names: %s", self.conf_file_name_pairs)

        self.ignore_config_dirs_config_files = ignore_config_dirs_config_files
        self.config_dirs = []
        for appd in app_dirs:
            self.config_dirs.extend(appd.site_config_dir.split(':'))
        for appd in app_dirs:
            self.config_dirs.append(appd.user_config_dir)

        self.config_file = config_file

        self.config_file_loader = ConfigFileLoader(self.conf_file_name_pairs, ignore_per_directory_config_files)
        self.dir_config = self.config_file_loader.dir_config
        # self.default_config_file_example = self.default_config_file.with_suffix('.example.py')

    @property
    def conf_file_names(self) -> list[str]:
        """Return possible configuration file names."""
        return list(itertools.chain.from_iterable(self.conf_file_name_pairs))

    def _config_file_pair_global_config(self, conf_dir: Path, conf_file_name_pair: tuple[str, str]) -> Path|None:
        """Load 'global' config from a config file."""

        cfg, cf_path = self.config_file_loader.read_and_validate_config_file_for_conf_file_pair(
            conf_dir, conf_file_name_pair, self._valid_config_dir_protect_scopes, self.ignore_config_dirs_config_files)
        self.global_config.protect_recursive |= cfg.get("global", set())
        return cf_path

    def load_config_dir_files(self) -> None:
        """Load config files from platform standard directories and specified config file, if any."""

        if not self.ignore_config_dirs_config_files:
            _LOG.debug("config_dirs: %s", self.config_dirs)
            for conf_dir in self.config_dirs:
                conf_dir = Path(conf_dir)
                if not conf_dir.exists():
                    continue

                for conf_file_name_pair in self.conf_file_name_pairs:
                    self._config_file_pair_global_config(conf_dir, conf_file_name_pair)

        if self.config_file:
            _LOG.debug("specified config_file: %s", self.config_file)
            conf_dir = self.config_file.parent.absolute()
            conf_name = self.config_file.name
            cf_path = self._config_file_pair_global_config(conf_dir, (conf_name, ""))
            if not cf_path:
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(self.config_file))

        _LOG.debug("Merged global config:\n %s", self.global_config)
