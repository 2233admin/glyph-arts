import sys

import pytest

from cli_charts import chart, splash


class _Stdout:
    def __init__(self, tty):
        self.tty = tty
        self.buffer = ""

    def isatty(self):
        return self.tty

    def write(self, text):
        self.buffer += text
        return len(text)

    def flush(self):
        return None


def test_splash_skipped_when_no_splash_flag(capsys):
    assert splash.main(["--no-splash"]) == 0
    assert capsys.readouterr().out == ""


def test_splash_skipped_when_env_var_set(monkeypatch, capsys):
    monkeypatch.setenv("GLYPH_ARTS_NO_SPLASH", "1")
    assert splash.main([]) == 0
    assert capsys.readouterr().out == ""


def test_splash_skipped_when_not_tty(capsys):
    assert splash.play_splash(stdout=_Stdout(False), sleep=lambda _: None) is False
    assert capsys.readouterr().out == ""


def test_splash_creates_sentinel_on_first_run(monkeypatch, tmp_path):
    monkeypatch.setattr(splash.Path, "home", lambda: tmp_path)
    stdout = _Stdout(True)
    assert splash.maybe_play_first_run(stdout=stdout, sleep=lambda _: None) is True
    assert splash.sentinel_path().exists()


def test_splash_skipped_when_sentinel_exists(monkeypatch, tmp_path):
    monkeypatch.setattr(splash.Path, "home", lambda: tmp_path)
    splash.sentinel_path().parent.mkdir(parents=True)
    splash.sentinel_path().write_text("shown\n", encoding="ascii")
    stdout = _Stdout(True)
    assert splash.maybe_play_first_run(stdout=stdout, sleep=lambda _: None) is False
    assert stdout.buffer == ""


def test_splash_command_always_plays(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "argv", ["glyph-arts", "splash"])
    monkeypatch.setattr(splash.Path, "home", lambda: tmp_path)
    splash.sentinel_path().parent.mkdir(parents=True)
    splash.sentinel_path().write_text("shown\n", encoding="ascii")
    stdout = _Stdout(True)
    monkeypatch.setattr(splash, "play_splash", lambda stdout=sys.stdout, sleep=None: stdout.write("played\n") or True)
    monkeypatch.setattr(sys, "stdout", stdout)
    with pytest.raises(SystemExit) as exc:
        chart.main()
    assert exc.value.code == 0
    assert stdout.buffer == "played\n"
