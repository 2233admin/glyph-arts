def test_bar_labels_values_aligned_after_sample():
    """For bar/pie-like dicts, sample preserves label[i] <-> value[i] pairing."""
    from cli_charts.chart import _sample_data

    data = {
        "labels": [f"L{i}" for i in range(100)],
        "values": list(range(100)),
    }
    out = _sample_data(data, 10)

    assert len(out["labels"]) == len(out["values"])
    for label, value in zip(out["labels"], out["values"]):
        assert int(label[1:]) == value, f"misalignment at {label} != {value}"
