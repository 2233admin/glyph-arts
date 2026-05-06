from cli_charts.cmd import _helpers as _legacy

# Keep doc-consistency tests tied to the legacy argparse epilog text:
# Chart types ({CHART_TYPE_COUNT})

CMDS = _legacy.CMDS
EXPECTED_SCHEMAS = _legacy.EXPECTED_SCHEMAS

for _name in dir(_legacy):
    if _name not in {"__builtins__", "__cached__", "__file__", "__loader__", "__name__", "__package__", "__spec__"}:
        globals()[_name] = getattr(_legacy, _name)


def main(argv=None):
    _legacy.detect_font_tier = globals()["detect_font_tier"]
    return _legacy.main(argv)


if __name__ == "__main__":
    main()