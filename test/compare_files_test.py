from pathlib import Path

from file_groups.compare_files import CompareFiles

from .conftest import same_content_files, different_content_files


@same_content_files("Hi", 'df/f11', 'ki/f12')
def test_compare_same(duplicates_dir):
    fcmp = CompareFiles()
    assert fcmp.compare(Path('df/f11'), Path('ki/f12'))


@different_content_files("oops", 'df/f11', 'ki/f12')
def test_compare_different_same_size_files(duplicates_dir):
    fcmp = CompareFiles()
    assert not fcmp.compare(Path('df/f11'), Path('ki/f12'))


@different_content_files("oops", 'df/f11', 'ki/f123')
def test_compare_different_different_size_files(duplicates_dir):
    # Test framework puts filename in files, so size is different when length is different
    fcmp = CompareFiles()
    assert not fcmp.compare(Path('df/f11'), Path('ki/f123'))
