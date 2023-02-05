import filecmp

from .types import FsPath


class CompareFiles():
    """Provides the basic interface needed by the filehandler when comparing files.

    This implementation simply does a filecmp.
    """

    def compare(self, fsp1: FsPath, fsp2: FsPath) -> bool:
        """Compare two files"""

        if fsp1.stat().st_size != fsp2.stat().st_size:
            return False

        return filecmp.cmp(fsp1, fsp2, shallow=False)
