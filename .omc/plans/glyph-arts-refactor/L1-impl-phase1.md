# L1 — Phase 1 Implementer: charts/_utils split

## 目的 (purpose statement)
这项工作将用于：**glyph-arts 重构 PR #1，团队 1 天内 review + merge**。读者是 repo maintainer + 一个独立 verifier。深度 = "清晰 + 最小 diff"，不是 "完美架构"。

## 项目上下文
- Repo: `D:/projects/glyph-arts` (branch `refactor/charts-split`)
- God file: `cli_charts/cmd/_helpers.py` — 2580 行，99 个 `def`，60+ 图表 + 15+ helper
- 目标: 把非图表 helper 抽到 `cli_charts/charts/_utils.py`
- 公共契约: `SKILL.md` (CLI 入口) 必须零变化

## WHEEL-FIRST GATE (mandatory, 5 行)
执行前花 30 秒确认：没有第三方库替代本次拆分 (这是纯文件重组，无业务逻辑)。如发现候选 wheel，写"wheels evaluated, none fit because [evidence]"。

## Scope — 严格只动这 3 个文件
| 文件 | 操作 | 行数目标 |
|---|---|---|
| `cli_charts/charts/__init__.py` | NEW | 5-10 行 (placeholder) |
| `cli_charts/charts/_utils.py` | NEW | 350-450 行 (从 _helpers 搬) |
| `cli_charts/cmd/_helpers.py` | EDIT | 删掉搬走的 helper + 改 import 路径 |

## 搬哪些 (exhaustive list, 不许漏不许多)
从 `cli_charts/cmd/_helpers.py` 行 52-417 范围，按函数定义顺序，搬这些 helper：

```
_symbol_tier  (line 52)
_bar_symbols  (line 57)
_style_to_bar_symbols  (line 75)
_style_to_gauge  (line 86)
_capture_stdout  (line 100)
_canvas_line  (line 106)
_has_flag  (line 141)
_rewrite_chat_argv  (line 145)
_rewrite_diagram_argv  (line 183)
_plt_finalize  (line 202)
_series_color  (line 244)
_statusline_values  (line 256)
_render_statusline  (line 272)
_catmull_pixels  (line 362)
_normalize_kline_dates  (line 403)
load_duckdb  (line 1757)
_textcharts_options  (line 1031)
_lttb  (line 1674)
_sample_indices  (line 1692)
_sample_data  (line 1702)
```

外加 `class _HiresCanvas` (line ~360) 也搬过去。

## 不许做 (硬禁令)
- 不动 `cli_charts/cmd/<name>.py` 任何 shim (50+ 文件, 都不许碰)
- 不动 `cli_charts/registry.py`
- 不动 `cli_charts/cmd/parser.py`, `media_args.py`, `media_dispatch.py`, `motion_commands.py`, `text_input_commands.py`, `direct_commands.py`, `tool_commands.py`, `animate_stream.py`, `textcharts.py`
- 不动 `SKILL.md`
- 不重构图表函数本身 (line/bar/scatter/... 仍留在 _helpers.py)
- 不加 docstring / type hint / 注释 (没要求就不要加)
- 不跑 `pytest` (本项目没装, 不要尝试 pip install)

## 完成定义 (Definition of Done)
1. `cli_charts/charts/__init__.py` 存在, 至少 import `from . import _utils`
2. `cli_charts/charts/_utils.py` 存在, 包含上面 20 个 helper + 1 个 class
3. `cli_charts/cmd/_helpers.py` 已删掉这些 helper, 顶部加 `from cli_charts.charts._utils import *` (如果 `from ... import *` 名字冲突, 显式列出 20 个名字)
4. **Bash smoke 跑通**:
   ```
   python -c "from cli_charts.charts._utils import _symbol_tier, _lttb, load_duckdb, _HiresCanvas; print('utils ok')"
   python -c "from cli_charts.cmd._helpers import line, bar, scatter, sparkline, kline; print('charts ok')"
   python -c "from cli_charts.cli import main; main(['line','--json','[1,2,3,4,5]'])" 2>&1 | head -3
   ```
   三个都返回非空 stdout / exit 0 = 成功
5. `git diff --stat` 显示 `_helpers.py` 净减少 ≥300 行
6. `git add -A && git commit -m "refactor: extract non-chart helpers to cli_charts.charts._utils (Phase 1)"`

## 失败处理
- smoke 第 1 条失败 → 看 ImportError 链, 缺的 helper 补到 `_utils.py`
- smoke 第 2 条失败 → `_helpers.py` import 路径没改对, 检查 `from cli_charts.charts._utils import ...`
- smoke 第 3 条失败 → `chart.py` 14 行 shim 的 `import _helpers` 链断了, Read 确认后改 import
- 任何"想顺手重构"的冲动 → 停下, 记到 progress.txt 后续 Phase 处理

## 输出格式
完工时输出：
- commit SHA
- 3 条 smoke 命令的实际 stdout (不是 "looks good")
- `git diff --stat` 末 5 行
- "Phase 1 完成, 等 verifier 接管" 一句话
