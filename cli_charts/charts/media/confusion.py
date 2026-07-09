"""confusion chart -- extracted from cli_charts.cmd._helpers (Phase 3b)."""

from cli_charts.charts._utils import _plt_finalize
from cli_charts.registry import register

@register("confusion")

def confusion(d, title, w, h, theme, **kw):
    """plotext ML confusion matrix.
    actual/predicted must be lists of class labels (int or str).
    """
    import plotext as plt
    actual_raw, predicted_raw = d['actual'], d['predicted']
    # plotext treats string xticks as dates and rejects them with a
    # %d/%m/%Y validation error. Map string labels to int indices and
    # synthesize a labels=[...] list so the user sees the original strings.
    if any(isinstance(v, str) for v in actual_raw) or any(isinstance(v, str) for v in predicted_raw):
        labels_in = d.get('labels') or sorted({str(v) for v in (*actual_raw, *predicted_raw)})
        index = {v: i for i, v in enumerate(labels_in)}
        actual = [index[str(v)] for v in actual_raw]
        predicted = [index[str(v)] for v in predicted_raw]
        labels = labels_in
    else:
        actual, predicted, labels = actual_raw, predicted_raw, d.get('labels')
    try:
        plt.confusion_matrix(actual, predicted, labels=labels)
    except ZeroDivisionError:  # plotext bug: M==m when all matrix cells are equal
        from collections import Counter

        from rich.console import Console
        from rich.table import Table
        actual, predicted = d['actual'], d['predicted']
        labs = d.get('labels') or sorted(set(actual) | set(predicted))
        counts = Counter(zip(actual, predicted, strict=False))
        t = Table(title=title or 'Confusion Matrix')
        t.add_column('actual \\ predicted')
        for p in labs:
            t.add_column(str(p))
        for a in labs:
            t.add_row(str(a), *[str(counts.get((a, p), 0)) for p in labs])
        Console().print(t)
        return
    _plt_finalize(plt, title, w, h, theme, kw)
