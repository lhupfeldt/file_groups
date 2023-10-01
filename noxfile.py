"""nox https://nox.thea.codes/en/stable/ configuration"""

# Use nox >= 2023.4.22

from pathlib import Path

import nox


_HERE = Path(__file__).absolute().parent
_TEST_DIR = _HERE/"test"
_PY_VERSIONS = ["3.12", "3.11", "3.10"]

nox.options.error_on_missing_interpreters = True


@nox.session(python=_PY_VERSIONS, reuse_venv=True)
def typecheck(session):
    session.install("-e", ".", "mypy>=1.5.1")
    session.run("mypy", "-v", str(_HERE/"src"))


@nox.session(reuse_venv=True)
def pylint(session):
    session.install(".", "pylint>=2.16.1", "pylint-pytest>=1.1.2")

    # TODO: enable checks
    disable_checks = "missing-module-docstring,missing-class-docstring,missing-function-docstring"
    session.run("pylint", "--disable", disable_checks, str(_HERE/"src"))
    disable_checks += ",multiple-imports,invalid-name"
    session.run("pylint", "--fail-under", "9.94", "--variable-rgx", r"[a-z_][a-z0-9_]{1,30}$", "--disable", disable_checks, str(_HERE/"test"))


@nox.session(python=_PY_VERSIONS, reuse_venv=True)
def unit(session):
    session.install(".", "pytest>=7.4.1", "coverage>=7.3.1", "pytest-cov>=4.1.0")
    session.run("pytest", "--cov", "--cov-report=term-missing", f"--cov-config={_TEST_DIR}/.coveragerc", *session.posargs)
