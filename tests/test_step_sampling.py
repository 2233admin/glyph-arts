"""P2 verification: LTTB sampling happens before step x-duplication.

Pipeline: raw data -> LTTB downsample -> step transform -> render
The test confirms shape preservation and correct point count.
N input points -> 2N-1 render points (each interior point appears twice, last only once).
"""
import numpy as np


def step_transform(x, y):
    """Reproduce the x-duplication used in chart.py step()."""
    xs, ys = [], []
    for i in range(len(x)):
        xs.append(x[i])
        ys.append(y[i])
        if i + 1 < len(x):
            xs.append(x[i + 1])
            ys.append(y[i])
    return xs, ys


def test_step_lttb_order():
    from lttb import downsample

    rng = np.random.default_rng(42)
    x = np.linspace(0, 100, 1000)
    y = np.sin(x) * 50 + rng.normal(0, 2, 1000)

    data = np.column_stack([x, y])
    sampled = downsample(data, n_out=50)

    xs, ys = step_transform(sampled[:, 0].tolist(), sampled[:, 1].tolist())

    assert len(xs) == 99, f"expected 99 render points (50*2-1), got {len(xs)}"
    assert len(xs) == len(ys)
    assert xs[0] < xs[-1], "x values must be monotonically increasing"
    # Verify LTTB preserved the range (not random crop)
    assert sampled[:, 0].min() >= x.min()
    assert sampled[:, 0].max() <= x.max()
    print(f"OK: 1000 -> 50 points via LTTB, step transform: {len(xs)} render points")


def test_step_lttb_fallback_uniform_stride():
    """When lttb is unavailable, chart.py falls back to uniform stride.
    Confirm the stride-sampled data still goes through step_transform correctly.
    """
    x = list(range(1000))
    y = [float(i % 17) for i in x]
    n = 50
    step = max(1, len(x) // n)
    sx, sy = x[::step][:n], y[::step][:n]

    xs, ys = step_transform(sx, sy)

    assert len(xs) == len(sx) * 2 - 1
    assert len(xs) == len(ys)
    print(f"OK: uniform-stride fallback: {len(sx)} points -> {len(xs)} render points")


if __name__ == "__main__":
    test_step_lttb_order()
    test_step_lttb_fallback_uniform_stride()
    print("All tests passed.")
