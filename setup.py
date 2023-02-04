from pathlib import Path

from setuptools import setup

_HERE = Path(__file__).resolve().parent

PROJECT_NAME = 'file_groups'
COPYRIGHT = u"Copyright (c) 2018 - 2020 Lars Hupfeldt Nielsen, Hupfeldt IT"
PROJECT_AUTHORS = u"Lars Hupfeldt Nielsen"
PROJECT_EMAILS = 'lhn@hupfeldtit.dk'
PROJECT_URL = "https://github.com/lhupfeldt/file_groups"
SHORT_DESCRIPTION = "Group files into 'protect' and 'work_on' and provide operations for safe delete/move and symlink handling."
LONG_DESCRIPTION = open(_HERE/"README.rst").read()

with open(_HERE/'requirements.txt') as ff:
    install_requires = [req.strip() for req in  ff.readlines() if req.strip() and req.strip()[0] != "#"]

if __name__ == "__main__":
    setup(
        name=PROJECT_NAME.lower(),
        version_command=('git describe', 'pep440-git'),
        author=PROJECT_AUTHORS,
        author_email=PROJECT_EMAILS,
        packages=['file_groups'],
        package_dir={'file_groups': 'src'},
        zip_safe=False,
        include_package_data=True,
        package_data={"file_groups": ["py.typed"]},
        python_requires='>=3.10',
        install_requires=install_requires,
        setup_requires='setuptools-version-command~=2.2',
        url=PROJECT_URL,
        description=SHORT_DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        long_description_content_type='text/x-rst',
        license='BSD',
        classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: BSD License',
            'Natural Language :: English',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
            'Topic :: Software Development :: Libraries',
        ],
    )
