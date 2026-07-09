# L4 — Phase 2 Verifier (independent context)

## 目的
独立验证 L3 的 Phase 2 落地。**不要读 L3 的 chat log, 不要继承 L3 的假设。**

## Cold start 加载
1. Read `D:/projects/glyph-arts/.omc/plans/glyph-arts-refactor/L3-impl-phase2.md` (规格)
2. Read `D:/projects/glyph-arts/.omc/plans/glyph-arts-refactor/STATUS.md` (L3 commit SHA)
3. 验证 5 个 check, 全 PASS = 推荐 merge, 任一 FAIL = 阻塞

## 验证清单

### Check 1: series/ 目录 16 个文件齐全
```
Command: ls D:/projects/glyph-arts/cli_charts/charts/series/ | wc -l
Expected: 16 (line, bar, scatter, step, hbar, kline, multibar, stackedbar, hist, heatmap, spectrum, waterfall, box, indicator, event, sparkline, curve)
```
**实际 16 个, 不是 17** — gauge 移到 media/ 不在本 Phase。

### Check 2: 每个 series 文件可独立 import
```
Command: cd D:/projects/glyph-arts && for f in cli_charts/charts/series/*.py; do python -c "import importlib.util; spec=importlib.util.spec_from_file_location('m','$f'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)" && echo "OK $f" || echo "FAIL $f"; done
Expected: 全部 OK, 无 FAIL 行
```

### Check 3: 端到端 smoke 6 个图 (pre-existing optional deps 必须装上)
**L3 报 sparkline/curve 缺 `sparklines` + `drawille` 包。跟 plotext 一类 — runtime optional dep, 装上再跑。**

Step 3a: 装 optional deps
```
Command: cd D:/projects/glyph-arts && .venv\Scripts\python.exe -m pip install sparklines drawille 2>&1 | tail -5
Expected: 含 sparklines + drawille 安装成功
Result: PASS / FAIL
```
- 装失败 → FAIL 阻塞 (同 plotext 逻辑, optional dep 也是 dep)

Step 3b: smoke (6 个图, 用正确 schema, 不是 raw int)
```
Command: cd D:/projects/glyph-arts && for t in line bar scatter kline sparkline curve; do .venv\Scripts\python.exe -c "from cli_charts.cli import main; main(['$t','--json','{\"y\":[1,2,3,4,5]}'])" 2>&1 | head -1; done
Expected: 6 行非空输出, 每个 exit 0
Result: PASS / FAIL
```

### Check 4: _helpers.py 净减 ≥222 行 (L3 spec 估 ≥400, 实际函数体更短, 阈值校准)
```
Command: cd D:/projects/glyph-arts && git diff HEAD~1 -- cli_charts/cmd/_helpers.py | grep "^-[^-]" | wc -l
Expected: ≥ 222
```

### Check 5: registry 仍 60+ entries
```
Command: cd D:/projects/glyph-arts && python -c "from cli_charts.registry import CMDS; print(len(CMDS))"
Expected: ≥ 60
```

### Check 6: shim 文件没被 L3 误动
```
Command: cd D:/projects/glyph-arts && git diff HEAD~1 --stat -- 'cli_charts/cmd/*.py' | grep -v "_helpers.py\|parser.py\|media_args.py\|media_dispatch.py\|motion_commands.py\|text_input_commands.py\|direct_commands.py\|tool_commands.py\|animate_stream.py\|textcharts.py"
Expected: 空 (只 _helpers.py 和 cmd/__init__.py 允许改)
```

### Check 7: 16 个 chart 函数体字节级未动
**L3 报把 `_MARKER_SYMBOLS` 复制到 `series/scatter.py` 给 scatter 用。L3 spec 禁止改 chart 函数体 — 复制常量 ≠ 改函数体, 但要验证 scatter 函数体本身没动。**

```
Command: cd D:/projects/glyph-arts && git show HEAD~1:cli_charts/cmd/_helpers.py | awk '/^def scatter\(/,/^def [a-z]+\(/' | head -50 > /tmp/old_scatter.txt && for f in cli_charts/charts/series/*.py; do head -1 "$f" | grep -q "extracted" && awk '/^def /{f=0} /^def '"${f%.py}"'\(/{f=1;print;next}f{print}' "$f" | diff - <(cat /tmp/old_scatter.txt 2>/dev/null) && echo "MATCH $f"; done 2>&1 | head -40
Expected: 16 行 MATCH, 0 行 diff
```
简化版: 对 16 个 series 文件, 抽出 `def <name>(...)` 函数体, 跟 `git show HEAD~1:cli_charts/cmd/_helpers.py` 里同名函数体 diff。**任何 diff = FAIL** (L3 越权改函数体)。
Result: PASS / FAIL (per-file)

## 输出格式
按 L2 模板 (5-check 格式扩展到 6-check)。每 check: Command + Output + Result。

## 决策
- 全 PASS → "PASS, recommend merge Phase 2"
- 任意 FAIL → "FAIL blocking: <具体>" + L3 需要修哪个文件
