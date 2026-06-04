import subprocess
import sys


def test_cmd_import_does_not_bootstrap_registry_by_default() -> None:
    code = """
import cli_charts.cmd
from cli_charts.registry import CMDS
print(len(CMDS))
cli_charts.cmd.bootstrap()
print("bar" in CMDS, "mermaid" in CMDS)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    lines = result.stdout.strip().splitlines()
    assert lines == ["0", "True True"]


def test_package_version_remains_available() -> None:
    code = "import cli_charts; print(cli_charts.__version__)"
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.stdout.strip()
