# L3 — Phase 2 Implementer: series/ leaves split

## 目的
Phase 1 已落地 `cli_charts/charts/_utils.py`。Phase 2 = 把 17 个 series 类图表 (line/bar/.../curve) 从 `cmd/_helpers.py` 搬到 `cli_charts/charts/series/`。**所有图表是 leaf, 互相无横向依赖**, 可以单文件搬。

## 前置确认 (mandatory)
开工前 Read `D:/projects/glyph-arts/.omc/plans/glyph-arts-refactor/STATUS.md` 确认 Phase 1 verifier = PASS。如果 L1 没 merge, **停**。

## Scope — 17 个 leaf
搬这些函数到 `cli_charts/charts/series/<name>.py` (每个一个文件):

```
line       (line 439)      bar          (line 492)
scatter    (line 454)      hbar         (line 511)
step       (line 471)      multibar     (line 573)
kline      (line 419)      stackedbar   (line 584)
hist       (line 595)      pie          (line 550)
heatmap    (line 605)      spectrum     (line 620)
waterfall  (line 630)      box          (line 640)
indicator  (line 654)      event        (line 664)
sparkline  (line 674)      curve        (line 1043)
gauge      (line 1080)     [独立, 但在 series 不合适, 放 media/]
```

`gauge` 例外 — 它不是 series, 是状态指示器, 改放 `cli_charts/charts/media/gauge.py`。本 Phase 只搬 series。

## 每个 .py 文件结构
```python
"""<name> chart — extracted from cli_charts.cmd._helpers (Phase 2)."""

from cli_charts.charts._utils import (
    # 只 import 该图表函数实际用到的 helper
    # 例如 line 用: _plt_finalize, _symbol_tier
)
from cli_charts.render.<engine> import <engine_func>  # 如果用


def <name>(data, title, w, h, theme, **kw):
    # 函数体, 跟 _helpers.py 里那个函数逐行一致
    ...
```

**严格: 函数体 0 修改。** 签名 0 修改。 docstring 如果原文件有就保留, 没有就不加。

## registry 钩子更新
`cli_charts/cmd/__init__.py` 的 `bootstrap()` 列表需要追加:
```python
"cli_charts.charts.series.line",
"cli_charts.charts.series.bar",
... 17 个
```

`cli_charts/cmd/<name>.py` 的 shim 文件**不许动** (Phase 5 才删)。

## 完成后处理
1. `cli_charts/cmd/_helpers.py` 删掉这 16 个函数 (gauge 在 Phase 4)
2. 顶部 import 改为 `from cli_charts.charts.series.<name> import <name>` (16 个)
3. `CMDS` dict 里的 `'<name>': <name>` 不变 (shim 文件继续 re-export)

## 验证 (do these before commit)
```bash
# 每个 series 文件独立 import
for f in cli_charts/charts/series/*.py; do
  python -c "import importlib.util, sys; spec=importlib.util.spec_from_file_location('m','$f'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('$f loaded')"
done

# 端到端 6 个图 smoke
python -c "from cli_charts.cli import main
for t in ['line','bar','scatter','kline','pie','sparkline']:
    main([t,'--json','[1,2,3,4,5]'])" 2>&1 | head -20
```

## 失败处理
- 函数体里有循环 import (例如 chart 调 chart) → 报告, 写到 progress.txt, 移到 Phase 3 处理
- helper 找不着 → 检查是否在 `_utils.py`, 不在 → 报告 (Phase 1 漏搬)
- 任何函数体微调冲动 → 禁止, 记到 progress.txt 后续清理

## 输出
- commit SHA
- `git diff --stat` 显示 `_helpers.py` 净减 ≥400 行
- 17 个文件每个的 line count
- smoke 输出末 10 行
- "Phase 2 完成, 等 verifier"
