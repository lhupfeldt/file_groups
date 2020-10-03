import filecmp

from .types import FsPath


class CompareFiles():
    """Provides the basic interface needed by the filehandler when comparing files.

    This implementation simply does a filecmp.
    """

    def compare(self, f1: FsPath, f2: FsPath) -> bool:
        """Compare two files"""

        if f1.stat().st_size != f2.stat().st_size:
            return False

        return filecmp.cmp(f1, f2, shallow=False)
