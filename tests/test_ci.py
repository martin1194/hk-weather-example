"""Lock the CI matrix to the Python versions the package supports."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ci_runs_oldest_supported_python():
    pyproject = (ROOT / "pyproject.toml").read_text()
    workflow = (ROOT / ".github/workflows/ci.yml").read_text()
    readme = (ROOT / "README.md").read_text()
    assert 'requires-python = ">=3.10"' in pyproject
    assert 'target-version = "py310"' in pyproject
    for version in ("3.10", "3.11", "3.12", "3.13"):
        assert f'"{version}"' in workflow
    assert "Python 3.10, 3.11, 3.12, and 3.13" in readme


def test_ci_uses_node24_actions():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text()
    readme = (ROOT / "README.md").read_text()
    assert "actions/checkout@v7" in workflow
    assert "actions/setup-python@v7" in workflow
    assert "Node.js 24" in readme


def test_ci_cancels_superseded_runs():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text()
    readme = (ROOT / "README.md").read_text()
    assert "cancel-in-progress: true" in workflow
    assert "group: ci-${{ github.workflow }}-${{ github.ref }}" in workflow
    assert "cancels the CI run that is still in progress" in readme
