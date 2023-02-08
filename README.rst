Library for grouping files into sets of 'work-on' and 'protect' based on arbitrarily nested directories.

Symlink safe delete and rename/move of files.
This library can be used for bulk fs cleanup programs.

You probably want to use the `FileHandler` or `FileHandlerCompare` class which provides the file operations.
The `FileGroups` class is quite lowlevel, and just does the split of file into `must_protect` and `may_work_on` sets.

Any use of these scripts are completely your own responsibility.
The author cannot be made responsible for any loss of data resulting from your use of these scripts.
