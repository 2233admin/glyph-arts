from cli_charts.registry import register


@register("video", schema_hint="path to video file")
def video(d, title, w, h, theme, **kw):
    raise NotImplementedError("video is handled directly by cli_charts.cmd._helpers.main")