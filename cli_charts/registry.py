from collections.abc import Callable

CMDS: dict[str, Callable[..., object]] = {}
EXPECTED_SCHEMAS: dict[str, str] = {}


def register(name: str, schema_hint: str = ""):
    def decorator(func: Callable[..., object]) -> Callable[..., object]:
        CMDS[name] = func
        EXPECTED_SCHEMAS[name] = schema_hint
        return func

    return decorator