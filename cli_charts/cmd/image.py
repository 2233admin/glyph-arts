from cli_charts.registry import register


@register("image", schema_hint="path to image file")
def image(d, title, w, h, theme, **kw):
    raise NotImplementedError("image is handled directly by cli_charts.cmd._helpers.main")