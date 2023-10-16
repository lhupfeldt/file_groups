import re

from file_groups.groups import FileGroups

from .conftest import same_content_files
from .utils.file_group_test_utils import FGC
from .config_files_test import set_conf_dirs, dir_conf_files


@same_content_files('A', 'ki/Af11.jpg', 'df/Bf11.jpg', 'ki/df/Af11.jpg', 'ki/ki/ki/ki/Af11.jpg')
@same_content_files('B', 'ki/df/KEEP_ME.JPEG', 'ki/df/NOT_ME.jpeg', 'df/df/KEEP_ME.jpg', 'df/df/df/df/KEEP_ME.jpg')
@same_content_files('C', 'df/AND_ME.JPG', 'df/df/AND_ME.JPG', 'df/df/df/And_Me.jpg', 'df/df/df/and_me.jpeg')
@same_content_files('D', 'df/df/df/df/gusr1.mpg', 'df/df/df/df/gusr1aaa.jpg', 'df/gsys2zzz.txt')  # Protected with "global" in condig dirs.
@same_content_files('F', 'df/imatchopt.hello', 'ki/df/df/IMATCHOPT.hi')  # Protected everywhere with 'protect' option
@same_content_files('G', 'df/P1a.jpg', 'df/P1.jpg', 'ki/df/P2.jpg', 'df/PR1.jpg', 'ki/df/P3.jpg')  # Protected with 'local' or 'recursive' in config dirs, so NOT here.
@dir_conf_files([], [r'KEEP_ME\..*'], 'ki/.file_groups.conf')
@dir_conf_files([r'KEEP_ME.jpg'], [r'(?i)and_me.jp[e]?g'], 'df/df/.file_groups.conf')
def test_file_groups_group_files_by_config_protect(duplicates_dir, set_conf_dirs):
    """'df/df/df/df/KEEP_ME.jpg' should NOT be protected,
       'df/df/KEEP_ME.jpg' should be protected,
       'ki/df/KEEP_ME.jpg' should be protected.
    """

    with FGC(FileGroups(['ki'], ['df', 'ki/df'], protect=[re.compile(r'(?i)imatchopt\..*$')]), duplicates_dir) as ck:
        assert ck.ckfl(
            'must_protect.files',
            'df/df/AND_ME.JPG', 'df/df/KEEP_ME.jpg', 'df/df/df/And_Me.jpg', 'df/df/df/and_me.jpeg',
            'df/df/df/df/gusr1aaa.jpg', 'df/gsys2zzz.txt', 'df/imatchopt.hello',
            'ki/Af11.jpg', 'ki/df/KEEP_ME.JPEG', 'ki/df/df/IMATCHOPT.hi', 'ki/ki/ki/ki/Af11.jpg')
        assert ck.ckfl(
            'may_work_on.files', 'df/AND_ME.JPG', 'df/Bf11.jpg', 'df/P1.jpg', 'df/P1a.jpg', 'df/PR1.jpg', 'df/df/df/df/KEEP_ME.jpg', 'df/df/df/df/gusr1.mpg',
            'ki/df/Af11.jpg', 'ki/df/NOT_ME.jpeg', 'ki/df/P2.jpg', 'ki/df/P3.jpg')
