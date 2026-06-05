"""sparkline_table chart -- extracted from cli_charts.cmd._helpers (Phase 3a)."""

from cli_charts.charts._utils import _textcharts_options


def sparkline_table(d, title, w, h, theme, **kw):
    """textcharts sparkline table -- multiple rows with inline mini charts.

    JSON: {"columns":["Revenue"],"values":{"Jan":[100],"Feb":[120],"Mar":[110]}}
    Note: Use 'sparkline' command for simpler sparkline charts.
    """
    import sys
    try:
        from textcharts import SparklineColumn, SparklineTable, SparklineTableData

        columns_data = d.get('columns', ['Value'])
        values = d.get('values', {})

        # Build columns with values dict
        columns = [SparklineColumn(name=str(col), values={}) for col in columns_data]

        # Build rows (labels) and populate column values
        rows = list(values.keys())

        for col_idx, col_name in enumerate(columns_data):
            for row_label in rows:
                if col_name in values and row_label in values[col_name]:
                    if col_idx < len(columns):
                        columns[col_idx].values[row_label] = values[col_name][row_label]

        data = SparklineTableData(rows=rows, columns=columns)
        chart = SparklineTable(data=data, title=title, options=_textcharts_options(kw))
        print(chart.render())
    except ImportError:
        print("ERROR:dep: pip install textcharts", file=sys.stderr)
        sys.exit(2)
