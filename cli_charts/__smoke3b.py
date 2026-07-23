"""Phase 3b smoke #4 v3: redirect all chart output to /dev/null, capture only summary."""
import io
import os
import sys
import contextlib

# All chart rendering must be suppressed
cases = [
    ("bar", ["bar", "--json", '{"labels":["A","B","C"],"values":[1,2,3]}']),
    ("hbar", ["hbar", "--json", '{"labels":["A","B","C"],"values":[1,2,3]}']),
    ("pie", ["pie", "--json", '{"labels":["A","B","C"],"values":[30,50,20]}']),
    ("table", ["table", "--json", '{"columns":["x","y"],"rows":[[1,2],[3,4]]}']),
    ("tree", ["tree", "--json", '{"tree":{"name":"root","children":[]}}']),
    ("gauge", ["gauge", "--json", '[{"label":"CPU","value":75,"max":100}]']),
    ("confusion", ["confusion", "--json", '{"actual":[0,1,2,0],"predicted":[0,2,1,0],"labels":["A","B","C"]}']),
    ("banner", ["banner", "HELLO"]),
    ("art", ["art", "hello"]),
    ("diagram", ["diagram", "--kind=math", "--expr=2+2"]),
    ("mermaid", ["mermaid", "graph TD; A-->B;"]),
    ("plotext", ["plotext", "--json", '{"x":[1,2,3],"y":[1,4,9]}']),
    ("incplot", ["incplot", "--json", '{"x":[1,2,3],"y":[1,4,9]}']),
    ("textplot", ["textplot", "--json", '{"x":[1,2,3],"y":[1,4,9]}']),
    ("turtle", ["turtle", "--code=forward 50"]),
    ("effect", ["effect", "matrix"]),
    ("uniplot", ["uniplot", "--json", '{"x":[1,2,3],"y":[1,4,9]}']),
    ("hires", ["hires", "--json", '{"labels":["A","B","C"],"values":[1,2,3]}']),
    ("radar", ["radar", "--json", '{"labels":["A","B","C"],"series":[{"label":"S","values":[1,2,3]}]}']),
    ("plotille", ["plotille", "--json", '{"x":[1,2,3],"y":[1,4,9]}']),
]

from cli_charts.cli import main

results = []
for name, args in cases:
    sink = io.StringIO()
    try:
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            main(args)
        results.append((name, "OK"))
    except SystemExit as e:
        results.append((name, f"exit:{e.code}"))
    except Exception as e:
        results.append((name, f"ERR:{type(e).__name__}:{str(e)[:60]}"))

ok = sum(1 for _, s in results if s == "OK")
print(f"OK: {ok}/{len(results)}")
for n, s in results:
    print(f"  {n}: {s}")
