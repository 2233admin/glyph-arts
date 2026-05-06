import re

from cli_charts import mascot


def test_mascot_has_20_frames():
    assert len(mascot.FRAMES) == 20


def test_mascot_frame_dimensions():
    for frame in mascot.FRAMES:
        rows = frame.splitlines()
        assert len(rows) == 11
        assert all(len(row) == 78 for row in rows)


def test_color_map_aligns_with_frames():
    assert len(mascot.COLOR_MAP) == len(mascot.FRAMES)
    for frame, color_frame in zip(mascot.FRAMES, mascot.COLOR_MAP, strict=True):
        rows = frame.splitlines()
        assert len(color_frame) == len(rows)
        for row, color_row in zip(rows, color_frame, strict=True):
            assert len(color_row) == len(row)


def test_color_roles_in_known_set():
    used_roles = {role for frame in mascot.COLOR_MAP for row in frame for role in row}
    assert used_roles <= mascot.ROLES


def test_render_to_string_no_ansi_when_not_tty():
    rendered = mascot.render_frame(0, tty=False)
    assert "\x1b[" not in rendered
    assert not re.search(r"\x1b\[[0-9;]*m", rendered)
    assert rendered == mascot.FRAMES[0]
