# L5 — Phase 3a Implementer: aggregates/ + composite/ + algebra/ split

## 目的
Phase 1 (charts/_utils.py) + Phase 2 (charts/series/, 16 files) 已落地。Phase 3a = 把 _helpers.py 里剩的 19 个非-series chart 函数搬到 `cli_charts/charts/{aggregates,composite,algebra}/`。**所有函数 0 body 改, 0 signature 改** — 跟 Phase 2 L3 同样的纪律。

## 前置确认 (mandatory)
开工前 Read `D:/projects/glyph-arts/.omc/plans/glyph-arts-refactor/STATUS.md` 确认 Phase 1 L2 + Phase 2 L4 = PASS。如果 L1/L3 没 merge, **停**。

## Scope — 19 functions, 3 subdirs

### `cli_charts/charts/aggregates/` (10 files, 1 fn each)
聚合统计/比较类 — 都不互相依赖, 可单文件搬:
```
graph                 (line 220)
comparison            (line 243)
diverging             (line 267)
summary               (line 285)
sparkline_table       (line 299)
cdf_chart             (line 331)
rank_table            (line 356)
percentile            (line 390)
boxplot_comparison    (line 435)
stacked_bar_text      (line 461)
```

### `cli_charts/charts/composite/` (3 files, 1 fn each)
多面板/合成/实时态:
```
panel                 (line 184)
dashboard             (line 562)
rich_live             (line 576)
```

### `cli_charts/charts/algebra/` (6 files, 1 fn each)
公式/状态/标定/波形:
```
formula               (line 1170)
formula_pretty        (line 1182)
calibrate             (line 1194)
status_command        (line 1110)
splash_command        (line 1120)
wave_command          (line 1160)
```

**不在本 Phase**: `bar`/`pie`/`table`/`gauge`/`banner`/`art_command`/...等 21 个 chart 函数 → 留给 Phase 3b media/ 搬。

## 每个 .py 文件结构 (跟 Phase 2 series/ 一致)
```python
"""<name> chart — extracted from cli_charts.cmd._helpers (Phase 3a)."""

from cli_charts.charts._utils import (
    # 只 import 该函数实际用到的 helper
)


def <name>(data, title, w, h, theme, **kw):
    # 函数体, 跟 _helpers.py 里那个函数逐行一致
    ...
```

**严格规则 (跟 L3 spec 一样):**
- 函数体 0 修改 (字节级一致)
- 签名 0 修改
- docstring: 原文件有就保留, 没有就不加
- import 块: 只 import 该函数实际用到的 helper (不要 `import *`)

## registry 钩子更新
`cli_charts/cmd/__init__.py` 的 `_MODULES` 列表需要追加 19 个 FQ path:
```python
"cli_charts.charts.aggregates.graph",
"cli_charts.charts.aggregates.comparison",
... 19 个
```

`bootstrap()` 已经在 commit 092e128 修复了 FQ path 识别 — 你直接添加 FQ path 即可, **不要再用 `cli_charts.cmd.xxx` 形式**。

`cli_charts/cmd/<name>.py` 的 shim 文件**不许动** (Phase 4 才删)。

## 完成后处理
1. `cli_charts/cmd/_helpers.py` 删掉这 19 个函数
2. 顶部 import 改为 `from cli_charts.charts.{aggregates,composite,algebra}.<name> import <name>` (19 个)
3. `CMDS` dict 里的 `'<name>': <name>` 不变 (shim 文件继续 re-export)
4. `_helpers.py` 还剩: 21 chart 类函数 (Phase 3b media) + 9 lowlevel + main + motion + system

## 验证 (do these before commit)
```bash
# 1. 每个新文件独立 import
for d in aggregates composite algebra; do
  for f in cli_charts/charts/$d/*.py; do
    python -c "import importlib.util; spec=importlib.util.spec_from_file_location('m','$f'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('$f loaded')"
  done
done

# 2. 端到端 smoke — 19 个图, 用正确 schema
# 已知依赖 (可能需要装): plotext (line, plotext), 别的应该都在 stdlib
.venv\Scripts\python.exe -m pip install plotext 2>&1 | tail -3

# 19 个 smoke, 每个用适合的 schema, 退出码 0
.venv\Scripts\python.exe -c "from cli_charts.cli import main
cmds = ['graph','comparison','diverging','summary','sparkline_table','cdf_chart','rank_table','percentile','boxplot_comparison','stacked_bar_text',
        'panel','dashboard','rich_live',
        'formula','calibrate','status','splash','wave','formula_pretty']
for t in cmds:
    try:
        main([t,'--json','{\"y\":[1,2,3,4,5]}'])
    except SystemExit: pass
    except Exception as e: print(f'  {t}: {type(e).__name__}: {e}')"

# 3. registry CMDS count 不变 (应该是 44)
python -c "from cli_charts.cmd import bootstrap; bootstrap(); from cli_charts.registry import CMDS; print('CMDS:', len(CMDS))"
```

## 失败处理
- 函数体有循环 import → 报告, 写到 progress.txt, 移到 Phase 4 处理
- helper 找不着 → 检查是否在 `_utils.py`, 不在 → 报告 (Phase 1 漏搬)
- 任何函数体微调冲动 → 禁止, 记到 progress.txt 后续清理
- 19 个 smoke 退出码非 0 → 报告 (不 commit)

## 输出
- commit SHA
- `git diff --stat` 显示 `_helpers.py` 净减 ≥150 行 (19 fns, 估计均值 ~20 行 + 函数体间空行)
- 19 个文件每个的 line count
- smoke 退出码汇总 (19/19 exit 0 = PASS)
- registry CMDS count = 44
- "Phase 3a 完成, 等 verifier"
