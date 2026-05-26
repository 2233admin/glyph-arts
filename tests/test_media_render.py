import contextlib
import subprocess

from PIL import Image

from cli_charts import media_render


def test_chafa_image_cmd_forces_symbol_output():
    cmd = media_render.build_chafa_image_cmd(40, 20, 'braille', no_color=True)

    assert cmd[:3] == ['chafa', '--format', 'symbols']
    assert cmd[cmd.index('--size') + 1] == '40x20'
    assert cmd[cmd.index('--symbols') + 1] == 'braille'
    assert cmd[cmd.index('--colors') + 1] == 'none'


def test_chafa_no_color_remaps_solid_blocks_to_braille():
    cmd = media_render.build_chafa_image_cmd(40, 20, 'block', no_color=True)

    assert cmd[cmd.index('--symbols') + 1] == 'braille'


def test_chat_image_preset_resolves_dense_safe_defaults():
    options = media_render.resolve_image_options(
        80, 20, None, False, 'contain', 'none', 'chat-hd',
    )

    assert options == (96, 48, 'braille', True, 'subject', 'anime')


def test_4k_chat_image_preset_uses_wide_inline_width():
    options = media_render.resolve_image_options(
        80, 20, None, False, 'contain', 'none', 'chat-4k',
    )

    assert options == (132, 66, 'braille', True, 'subject', 'anime')


def test_terminal_image_preset_uses_terminal_columns_override():
    options = media_render.resolve_image_options(
        80, 20, None, False, 'contain', 'none', 'terminal', cols=220,
    )

    assert options == (218, 109, 'braille', True, 'subject', 'anime')


def test_terminal_image_preset_accepts_columns_env(monkeypatch):
    monkeypatch.setenv('GLYPH_ARTS_COLS', '180')
    options = media_render.resolve_image_options(
        80, 20, None, False, 'contain', 'none', 'terminal',
    )

    assert options == (178, 89, 'braille', True, 'subject', 'anime')


def test_terminal_image_preset_allows_explicit_ink_filter():
    options = media_render.resolve_image_options(
        80, 20, None, False, 'contain', 'ink', 'terminal', cols=100,
    )

    assert options == (98, 49, 'braille', True, 'subject', 'ink')


def test_render_image_uses_chat_safe_chafa_command(monkeypatch, capsys):
    captured = {}

    monkeypatch.setattr(media_render.shutil, 'which', lambda name: name)

    @contextlib.contextmanager
    def fake_prepared_path(path, fit, filter_style):
        captured['fit'] = fit
        captured['filter_style'] = filter_style
        yield path

    def fake_run(cmd, capture_output, text):
        captured['cmd'] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout='pixels\n', stderr='')

    monkeypatch.setattr(media_render, '_prepared_image_path', fake_prepared_path)
    monkeypatch.setattr(media_render.subprocess, 'run', fake_run)

    media_render.render_image('avatar.jpg', 24, 12, 'braille', True, 'subject', 'anime')

    assert captured['fit'] == 'subject'
    assert captured['filter_style'] == 'anime'
    assert captured['cmd'][:3] == ['chafa', '--format', 'symbols']
    assert captured['cmd'][-1] == 'avatar.jpg'
    assert 'pixels' in capsys.readouterr().out


def test_anime_filter_prepares_grayscale_quantized_image(tmp_path):
    src = tmp_path / 'source.png'
    Image.new('RGB', (4, 4), (30, 40, 50)).save(src)

    with media_render._prepared_image_path(str(src), 'contain', 'anime') as filtered:
        assert filtered != str(src)
        with Image.open(filtered) as im:
            assert im.mode == 'L'
            assert im.size == (4, 4)


def test_ink_filter_inverts_white_page_for_dark_terminal(tmp_path):
    src = tmp_path / 'formula.png'
    im = Image.new('RGB', (4, 4), 'white')
    im.putpixel((1, 1), (0, 0, 0))
    im.save(src)

    with media_render._prepared_image_path(str(src), 'contain', 'ink') as filtered:
        assert filtered != str(src)
        with Image.open(filtered) as out:
            assert out.mode == 'L'
            assert out.getpixel((0, 0)) < out.getpixel((1, 1))


def test_foreground_bbox_detects_center_subject():
    width, height = 12, 12
    pixels = bytearray()
    for y in range(height):
        for x in range(width):
            if 4 <= x < 8 and 3 <= y < 9:
                pixels.extend((220, 120, 60))
            else:
                pixels.extend((2, 8, 18))

    bbox = media_render._foreground_bbox_from_rgb(bytes(pixels), width, height)

    assert bbox == (4, 3, 8, 9)
