"""Change logging of Path objects."""

from os import DirEntry
from pathlib import Path
from collections.abc import Collection, Mapping
from typing import Any, cast


class PathDisplay:
    """Functions to change how paths are displayed.

    E.g. Show paths relative or absolute and/or show home dir as '~'.
    """

    def __init__(self, *, home_tilde: bool = True, rel_path: bool = True):
        super().__init__()
        self.home_tilde = home_tilde
        self.rel_path = rel_path
        self.home_dir_str = str(Path.home())
        self.cwd_dir_str = f"{Path.cwd()}/"

    def __eq__(self, other: Any) -> bool:
        return (self.home_tilde == other.home_tilde and self.rel_path == other.rel_path) if isinstance(other, PathDisplay) else False

    def _handle_str_home_tilde(self, path_str: str, *, count: int = 1) -> str:
        """Replace user home dir in a str with a '~'."""
        return path_str.replace(self.home_dir_str, '~', count) if self.home_tilde else path_str

    def handle_str(self, path_str: str, *, count: int = 1) -> str:
        """Replace cwd() or user home dir in a str with '' or a '~'."""
        if self.rel_path:
            path_str = path_str.replace(self.cwd_dir_str, '', count)

        return self._handle_str_home_tilde(path_str, count=count)

    def handle_path(self, abs_path: Path) -> str:
        """Handle Paths."""
        try:
            if self.rel_path:
                return str(abs_path.relative_to(self.cwd_dir_str))
        except ValueError:
            # Not relative
            pass

        return self._handle_str_home_tilde(str(abs_path))

    def handle_mapping(self, arg: Mapping) -> Mapping:
        """Handle mappings."""
        replaced_home = {self.handle_any(key): self.handle_any(val) for key, val in arg.items()}
        try:
            if default_factory := getattr(arg, "default_factory", None):
                # A defaultdict needs the default_factory arg for __init__.
                return type(arg)(default_factory, replaced_home)  # type: ignore[call-arg]

            return type(arg)(replaced_home)  # type: ignore[call-arg]
        except TypeError:
            # Could happen for a dict subtype without a constructor from a dict.
            # I.e. defaultdict does not have that (but is is correctly handled now).
            return replaced_home

    def handle_tuple(self, arg: tuple) -> tuple:
        """Handle tuples."""
        try:
            # typing.NamedTuple
            return type(arg)(**{self.handle_any(key): self.handle_any(val) for key, val in arg._asdict().items()})  # type: ignore[attr-defined]
        except AttributeError:
            return type(arg)([self.handle_any(val) for val in arg])

    def handle_set(self, arg: set) -> set|tuple:
        """Handle set types.

        Note: Sets may be converted to tuple to avoid changing the size of the set when items with the same repr are converted to str.
        """

        res = cast(set, self.handle_collection(arg))
        return res if len(res) == len(arg) else self.handle_tuple(tuple(arg))

    def handle_collection(self, arg: Collection) -> Collection:
        """Handle collection types."""
        return type(arg)([self.handle_any(val) for val in arg])  # type: ignore[call-arg]

    def handle_any(self, arg: Any) -> Any:
        """Handle any type."""
        match arg:
            case Path():
                return self.handle_path(arg)
            case DirEntry():
                return self.handle_path(Path(arg.path))
            case str():
                return self.handle_str(arg, count=-1)
            case Mapping():
                return self.handle_mapping(arg)
            case tuple():
                return self.handle_tuple(arg)
            case set():
                return self.handle_set(arg)
            case Collection():
                return self.handle_collection(arg)
            case Exception():
                return self.handle_str(str(arg), count=-1)

        return arg
