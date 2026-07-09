# L7 — Phase 3b Implementer (media/ split)

## 目的
继续 Phase 3 的 `_helpers.py` 收口。本 Phase 把剩下的 20 个真实 chart 叶子函数从 `cli_charts/cmd/_helpers.py` 搬到 `cli_charts/charts/media/<name>.py`。

**Phase 3 收口后状态**: `_helpers.py` 只剩 16 个 `*_command` 占位 stub + 9 个 `_*` helper + main = 25 个 def。Phase 4 (L9) 才是把这些搬出/建 `_dispatch.py` 的活。

## 范围 (20 chart fns → `cli_charts/charts/media/`)

| 名 | shim 名 | 类型 | 当前行号 (git show edd9b7b) | 备注 |
|---|---|---|---|---|
| bar | bar | 真实 | `_helpers.py:33` | 顶层 plotext bar, 委派到 hbar/text |
| hbar | hbar | 真实 | `_helpers.py:54` | 水平 bar (textgraph/ascii-graph) |
| pie | pie | 真实 | `_helpers.py:79` | rich percentage-bar |
| table | table | 真实 | `_helpers.py:104` | rich double-edge 表格 |
| tree | tree | 真实 | `_helpers.py:135` | rich Tree 嵌套数据 |
| gauge | gauge | 真实 | `_helpers.py:172` | rich multi-metric progress bars (L3 预规划放 media/) |
| confusion | confusion | 真实 | `_helpers.py:225` | plotext ML confusion matrix |
| banner | banner | 真实 | `_helpers.py:269` | pyfiglet ASCII banner |
| art_command | art | 真实 | `_helpers.py:301` | text art 渲染 (含 list_fonts/list_decors 分支, **不是**占位 stub) — shim 名是 `art` |
| diagram | diagram | 真实 | `_helpers.py:344` | diagon-compatible |
| mermaid | mermaid | 真实 | `_helpers.py:384` | beautiful-mermaid 渲染 |
| plotext | plotext | 真实 | `_helpers.py:413` | plotext overlay (error bars / dates) |
| incplot | incplot | 真实 | `_helpers.py:437` | incplot-style auto renderer |
| textplot | textplot | 真实 | `_helpers.py:480` | textplots-rs 连续函数 |
| turtle | turtle | 真实 | `_helpers.py:511` | drawille-style turtle |
| effect | effect | 真实 | `_helpers.py:551` | chat-first 视觉效果预设 |
| uniplot | uniplot | 真实 | `_helpers.py:604` | uniplot 科研 line/scatter |
| hires | hires | 真实 | `_helpers.py:649` | 24-bit braille 高分辨率 |
| radar | radar | 真实 | `_helpers.py:685` | 极坐标雷达图 |
| plotille_chart | plotille | 真实 | `_helpers.py:728` | plotille Figure 复合 braille — shim 名是 `plotille` |

> **shim 名 ≠ 函数名 的 2 个**:
> - 函数 `art_command` → shim 名 `art` (因为 argparse 命令是 `art`)
> - 函数 `plotille_chart` → shim 名 `plotille` (因为 argparse 命令是 `plotille`)
> registry 按**函数名** key (`CMDS[函数名]`), shim 内部用 `register("art")(art_command)` 重命名注册。

**严格不搬** (main() 内部特殊 dispatch 的占位 stub, Phase 4 处理):
`animate_command, record_command, record_replay_command, to_hyperframes_command, to_ascii_motion_command, code_command, demo_command, gallery_command, auto_command, live_command, doctor_command, install_backends_command, fonts_command, chat_health_command, serve_command` (16 个)

**严格不搬** (Phase 4 范围):
`_build_cli_epilog, _print_dependency_status, _print_style_list, _handle_pre_parse_flags, _apply_font_and_style_defaults, _load_ascii_motion_adapter, _require_ascii_motion_npx, _render_ascii_motion_frames, _build_arg_parser, main` (10 个)

## 强制规则 (从 L5 regression 学到的)

### 🚨 **CRITICAL #1: 绝对禁止 `from x import y` 形式搬函数 🚨**

**L5 复盘**: L5 implementer 用 `from cli_charts.charts.aggregates.graph import graph` 把 19 个函数搬过去, 错把新文件当成"纯 import 转发"来用, 函数的 `def` 不在 `cli_charts.charts.aggregates.graph` 模块的模块级 `def` 列表里, @register 装饰器**不触发**。结果 `cli_charts.registry.CMDS` 从 44 掉到 32, 4 个调用方 (gallery / demo / animate / rich_live) 全部掉链。Lead hotfix 0685159 用了 50 行脚本来逐文件补装饰器, 才把 CMDS 救回到 51。

**本 Phase 唯一允许的搬迁形式 (在每个新文件里)**:
```python
# cli_charts/charts/media/bar.py  (L7 implementer 创建)
"""bar chart -- extracted from cli_charts.cmd._helpers (Phase 3b)."""

from cli_charts.registry import register


@register("bar")

def bar(d, title, w, h, theme, **kw):
    """plotext vertical/horizontal bar chart."""
    # 函数体 0 修改 (从 _helpers.py 完整复制)
    ...
```

每个新文件的 `def` 必须是该模块的**模块级** def, @register 装饰器才能在 import 时触发表 `CMDS[name] = func` 的赋值。**禁止**:
- `from cli_charts.cmd._helpers import bar` 然后再 `def bar(...): ...` 重新包装 (re-export 不触发装饰器)
- `from cli_charts.charts.media.bar import bar` 在 `_helpers.py` 里再 re-export (同问题)
- 任何"import 转发 + 不装饰" 模式

**校验** (implementer 自检): `python -c "import cli_charts.charts.media.bar; from cli_charts.registry import CMDS; assert CMDS['bar'] is cli_charts.charts.media.bar.bar"` 必须通过。

### 🚨 **CRITICAL #2: 绝对禁止只改 import 路径不动函数体 🚨**

L5 implementer 的另一个诱惑: 既然函数体不动, 是不是可以把函数留在 `_helpers.py`, 改成在 `_helpers.py` 里 `from cli_charts.charts.media.bar import bar` 然后 re-export? **禁止**。这样 `_helpers.py` 没有真正瘦下来, 等于没搬。L7 必须是真搬家 (函数 def 整体移出 _helpers.py)。

### 🚨 **CRITICAL #3: shim 必须改 import 路径 🚨**

Phase 1/2 留的 20 个 shim 文件 (`cli_charts/cmd/<shim_name>.py`) 当前形式是:
```python
# e.g. cli_charts/cmd/bar.py
from cli_charts.cmd._helpers import bar
from cli_charts.registry import register
register("bar")(bar)
```

搬完后 `_helpers.py` 已经没有 `bar` 了, shim 走 `from cli_charts.cmd._helpers import bar` 会 ImportError, shim 整个加载失败 → 间接导致 `from cli_charts.cmd import bar` 失败, 以及 `_MODULES` 里 `"bar"` 这个短名解析失败 (短名走 `import_module(f"{__name__}.{module}")` = `import_module("cli_charts.cmd.bar")` → cli_charts/cmd/bar.py → ImportError)。

**L7 必须改 shim**: 把 `from cli_charts.cmd._helpers import <name>` 改为 `from cli_charts.charts.media.<new_module> import <new_func>`, 同时**删除 shim 里的 `register(...)` 调用** (单一注册源, 避免重复, 也避免 shim 名 vs 函数名 mismatch 时的双 key 噪声)。

**shim 改写模板** (20 个, 1-2 行/文件):

| shim 文件 | 改前 (L7 implementer 不要保留) | 改后 |
|---|---|---|
| `cli_charts/cmd/bar.py` | `from cli_charts.cmd._helpers import bar`<br>`from cli_charts.registry import register`<br>`register("bar")(bar)` | `from cli_charts.charts.media.bar import bar` |
| `cli_charts/cmd/art.py` | `from cli_charts.cmd._helpers import art_command`<br>`from cli_charts.registry import register`<br>`register("art")(art_command)` | `from cli_charts.charts.media.art_command import art_command as art` |
| `cli_charts/cmd/plotille.py` | `from cli_charts.cmd._helpers import plotille_chart`<br>`from cli_charts.registry import register`<br>`register("plotille")(plotille_chart)` | `from cli_charts.charts.media.plotille_chart import plotille_chart as plotille` |
| 其他 17 个 | 同 bar.py 形式 (shim 名 = 函数名) | 同 bar.py 形式 |

**改后 shim 形式** (单行 re-export):
```python
# cli_charts/cmd/bar.py (改后)
from cli_charts.charts.media.bar import bar
```

**L7 implementer 校验**: `python -c "import cli_charts.cmd; from cli_charts.registry import CMDS; assert CMDS['bar'] is cli_charts.charts.media.bar.bar"` 必须通过 (单一来源: media/bar.py 的 @register)。

### 函数体 0 修改
- 函数签名 0 修改
- 函数 docstring 0 修改
- 函数体内部代码 0 修改
- 只能做这些移动/添加: (a) 文件顶部 docstring (1 行), (b) `from cli_charts.registry import register`, (c) `@register("<name>")` 装饰器, (d) 装饰器与 `def` 之间的空行

**L6 验证经验**: 19 个文件 +3 行 (import + decorator + blank) 才是合规。3 字节级 diff 算 OK (graph 的注释微调、dashboard 的 1 级路径加深、rich_live 的 CMDS import shim) 但**要逐个在 commit message 写明**。本 Phase 20 个新文件期望 +3 行/文件, 0 字节级函数体 diff。

### _MODULES 列表更新
`cli_charts/cmd/__init__.py` 的 `_MODULES` 列表需要把 20 个 media 路径改写为 FQ 形式 (用函数名, 不是 shim 名):

**改前 → 改后**:
```
"bar"               → "cli_charts.charts.media.bar"
"pie"               → "cli_charts.charts.media.pie"
"table"             → "cli_charts.charts.media.table"
"tree"              → "cli_charts.charts.media.tree"
"gauge"             → "cli_charts.charts.media.gauge"
"confusion"         → "cli_charts.charts.media.confusion"
"diagram"           → "cli_charts.charts.media.diagram"
"mermaid"           → "cli_charts.charts.media.mermaid"
"plotext"           → "cli_charts.charts.media.plotext"
"incplot"           → "cli_charts.charts.media.incplot"
"textplot"          → "cli_charts.charts.media.textplot"
"turtle"            → "cli_charts.charts.media.turtle"
"effect"            → "cli_charts.charts.media.effect"
"uniplot"           → "cli_charts.charts.media.uniplot"
"hires"             → "cli_charts.charts.media.hires"
"radar"             → "cli_charts.charts.media.radar"
"banner"            → "cli_charts.charts.media.banner"
"art"               → "cli_charts.charts.media.art_command"  (函数名!)
"plotille"          → "cli_charts.charts.media.plotille_chart"  (函数名!)
```

**`hbar`** 不在当前 `_MODULES` 里, 需要新增:
```
"cli_charts.charts.media.hbar"
```

`_MODULES` 改写后, `bootstrap()` 的 FQ 检测 (`module.startswith("cli_charts.")`) 直接 `import_module(module)` 走 media/ 的新文件。

## 不动的文件 (L7 implementer 严格遵守)
- `cli_charts/cmd/_helpers.py` 里: 16 个 `*_command` stub + 9 个 `_*` helper + main (Phase 4)
- `cli_charts/charts/series/` (Phase 2 完毕, 不动)
- `cli_charts/charts/aggregates/` `composite/` `algebra/` (Phase 3a 完毕, 不动)
- `cli_charts/charts/_utils.py` (Phase 1 完毕, 不动)
- `cli_charts/registry.py` (不改)
- `cli_charts/cli.py` (不改)
- `cli_charts/cmd/_dispatch.py` (Phase 4 才创建)

## 端到端 smoke (实施后必须跑)

1. **20 个新文件存在**: `ls cli_charts/charts/media/*.py | wc -l` = 20
2. **20 个新文件可独立 import + @register 触发**:
   ```
   cd D:/projects/glyph-arts && .venv\Scripts\python.exe -c "
   from cli_charts.cmd import bootstrap; bootstrap()
   from cli_charts.registry import CMDS
   expected = ['bar','hbar','pie','table','tree','gauge','confusion','banner','art_command','diagram','mermaid','plotext','incplot','textplot','turtle','effect','uniplot','hires','radar','plotille_chart']
   missing = [n for n in expected if n not in CMDS]
   non_callable = [n for n in expected if n in CMDS and not callable(CMDS[n])]
   print('CMDS count:', len(CMDS), '(expected 51 + 20 = 71)')
   print('missing:', missing if missing else 'none')
   print('non_callable:', non_callable if non_callable else 'none')
   "
   ```
   预期: count=71, missing=none, non_callable=none
3. **shim 反向 import 链**:
   ```
   cd D:/projects/glyph-arts && .venv\Scripts\python.exe -c "
   import cli_charts.cmd.bar, cli_charts.cmd.pie, cli_charts.cmd.gauge
   import cli_charts.cmd.art, cli_charts.cmd.plotille
   print('shims import OK')
   "
   ```
   预期: 无 ImportError
4. **20 个 smoke (每个函数跑一次)**:
   ```
   cd D:/projects/glyph-arts && .venv\Scripts\python.exe -c "
   from cli_charts.cli import main
   cmds = ['bar','hbar','pie','table','tree','gauge','confusion','banner','art','diagram','mermaid','plotext','incplot','textplot','turtle','effect','uniplot','hires','radar','plotille']
   for t in cmds:
       try: main([t,'--json','{\"y\":[1,2,3,4,5]}'])
       except SystemExit as e: print(f'{t}: exit {e.code}')
       except Exception as e: print(f'{t}: ERR {type(e).__name__}: {e}')
   "
   ```
   预期: ≥ 15/20 exit 0; 允许 ≤ 5 个 fail (env dep, e.g. rich/regex/gauge/pyfiglet/plotext 未装), 失败必须明确分类 (env dep not refactor regression)
5. **`_helpers.py` 净减行数**: `git diff edd9b7b -- cli_charts/cmd/_helpers.py | grep -E '^-[^-]' | wc -l` 预期 ≥ 200 行 (L5 spec 估计 ≥ 300, 但函数体大小有差异, 200 是底线)

## 不允许 L7 implementer 做的事
- ❌ 改 `_helpers.py` 里 16 个 `*_command` stub 的代码 (Phase 4)
- ❌ 改 `_helpers.py` 里 9 个 `_*` helper + main (Phase 4)
- ❌ 创建 `cli_charts/cmd/_dispatch.py` (Phase 4)
- ❌ 创建 `cli_charts/charts/media/__init__.py` (不需要, 跟 series/ aggregates/ 一样)
- ❌ 加 type hints / docstring / 注释 (没要求就不加, 跟 Phase 1/2/3a 一致)
- ❌ 改 `cli_charts/registry.py` (禁止)
- ❌ 改 `cli_charts/cli.py` (禁止)
- ❌ 改任何 shim 文件除了那 20 个 (`auto.py` `live.py` `candlestick.py` `image.py` `video.py` `serve.py` 等 6 个不是 media 范围的, 严格不动)
- ❌ 顺手重构 _helpers.py 里其他代码 (Kantorovich 原则: 别加没被要求的东西)

## Decision Rule (实施完成后自检)
- CMDS count == 71 (51 + 20) → **PASS, ready for L8 verifier**
- CMDS count ∈ [65, 70] → 缺几个, follow-up 补
- CMDS count < 65 → **FAIL, 必有 L5 类 regression, 回查**
- shim 反向 import chain 断 → **FAIL, shim 改写不完整**

## Commit message 模板
```
refactor(phase3b): extract 20 chart leaves to cli_charts/charts/media/

- 20 new files in cli_charts/charts/media/ (bar/hbar/pie/table/tree/gauge/
  confusion/banner/art_command/diagram/mermaid/plotext/incplot/textplot/
  turtle/effect/uniplot/hires/radar/plotille_chart)
- Each file: @register("<name>") decorator on module-level def
  (L5 lesson: 'from x import y' doesn't trigger @register)
- _MODULES list in cli_charts/cmd/__init__.py: 20 entries migrated to FQ
  paths (cli_charts.charts.media.<name>)
- 20 shim files in cli_charts/cmd/<name>.py: import path updated to
  media/ location, register(...) call removed (single source of truth)
- hbar newly added to _MODULES
- _helpers.py: net -200+ lines (16 *_command stubs + 9 _* helpers + main
  left for Phase 4)
- CMDS count: 51 -> 71

[Phase 3b L7 implementer]
```

## 失败 / 不确定时的回退
- 任何新文件 import 时报 `ModuleNotFoundError: cli_charts.charts.media.<name>` → 检查 `_MODULES` 是不是漏写
- `CMDS[<name>] is not <function>` → 检查 shim 是不是忘了删 `register(...)` 调用 (double-register 会后写覆盖前写, 不会错, 但浪费)
- `_helpers.py` 报 `ImportError: cannot import name 'bar'` → shim 改写漏了某个

## 上传状态
完成后:
1. `git add cli_charts/charts/media/ cli_charts/cmd/__init__.py cli_charts/cmd/*.py cli_charts/cmd/_helpers.py`
2. `git status -s` 确认无意外文件
3. `git commit -m "..."` (用上面模板)
4. 把 commit SHA 填到 STATUS.md "Phase 3b — L7 implementer" 节
5. 通知 lead 准备 L8 verifier
