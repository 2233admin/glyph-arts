import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_PLOTEXT_DEPENDENT = {
    "test_animation.py",
    "test_confusion.py",
}


@pytest.fixture(autouse=True)
def _skip_plotext_dependent_tests(request):
    if Path(str(request.fspath)).name in _PLOTEXT_DEPENDENT:
        if importlib.util.find_spec("plotext") is None:
            pytest.skip("plotext not installed; rerun with `pip install -e .`")
    if Path(str(request.fspath)).name == "test_rich_live.py":
        if importlib.util.find_spec("sparklines") is None:
            pytest.skip("sparklines not installed; rerun with `pip install -e .`")
