from pathlib import Path

import nox


_HERE = Path(__file__).absolute().parent
_TEST_DIR = _HERE/"test"
_PY_VERSIONS = ["3.11", "3.10"]

nox.options.error_on_missing_interpreters = True


@nox.session(python=_PY_VERSIONS, reuse_venv=True)
def typecheck(session):
    session.install("-e", ".", "-r", str(_TEST_DIR/"mypy_requirements.txt"))
    session.run("mypy", "-v", str(_HERE/"src"))


@nox.session(reuse_venv=True)
def pylint(session):
    session.install(".", "-r", str(_TEST_DIR/"pylint_requirements.txt"))

    # TODO: enable checks
    disable_checks = "missing-module-docstring,missing-class-docstring,missing-function-docstring"
    session.run("pylint", "--disable", disable_checks, str(_HERE/"src"))
    disable_checks += ",multiple-imports,invalid-name"
    session.run("pylint", "--fail-under", "9.94", "--variable-rgx", r"[a-z_][a-z0-9_]{1,30}$", "--disable", disable_checks, str(_HERE/"test"))


@nox.session(python=_PY_VERSIONS, reuse_venv=True)
def unit(session):
    session.install(".", "-r", str(_TEST_DIR/"requirements.txt"))
    session.run("pytest", "--cov", "--cov-report=term-missing", f"--cov-config={_TEST_DIR}/.coveragerc", *session.posargs)
