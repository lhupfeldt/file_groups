from pathlib import Path

import nox


_HERE = Path(__file__).absolute().parent
_TEST_DIR = _HERE/'test'
_PY_VERSIONS = ['3.11', '3.10']

nox.options.error_on_missing_interpreters = True


@nox.session(reuse_venv=True)
def typecheck(session):
    session.install('-r', str(_HERE/'requirements.txt'), '-r', str(_TEST_DIR/'mypy_requirements.txt'))
    session.run('mypy', '-v', str(_HERE/'src'))


@nox.session(reuse_venv=True)
def pylint(session):
    session.install('.')
    session.install('-r', str(_HERE/'requirements.txt'), '-r', str(_TEST_DIR/'pylint_requirements.txt'))

    session.run('pylint', str(_HERE/'src'))
    session.run('pylint', '--fail-under', '9.99', str(_HERE/'test'))


@nox.session(python=_PY_VERSIONS, reuse_venv=True)
def unit(session):
    session.install('.')
    session.install('-r', str(_HERE/'requirements.txt'), '-r', str(_TEST_DIR/'requirements.txt'))
    session.run('pytest', "--cov", "--cov-report=term-missing", f"--cov-config={_TEST_DIR}/.coveragerc", *session.posargs)
