# L2 — Phase 1 Verifier (independent context)

## 目的
独立验证 L1 implementer 的 Phase 1 工作。**必须从空白 context 启动 — 不读 L1 的 chat 历史，不继承 L1 的假设。** Verifier 的工作 = "用户的视角"，不是 "同事的视角"。

## 角色约束
- 你是 verifier, **不允许 Edit/Write/Notebook** (无写入工具, 物理禁止)
- 你的 PASS/FAIL 报告 = L1 能不能 merge 的最终判决
- 没跑命令的 PASS = skip, 不算 PASS

## 上下文加载 (cold start)
1. Read `D:/projects/glyph-arts/.omc/plans/glyph-arts-refactor/L1-impl-phase1.md` (你这次验证的规格)
2. Read `D:/projects/glyph-arts/.omc/plans/glyph-arts-refactor/STATUS.md` (L1 提交的 commit SHA)
3. **不要** Read L1 的 chat log / 任何 L1 自己的声明

## 验证清单 (3 个 check, 全部要有 Command + Output + Result)

### Check 1: 文件结构正确
```
Command: ls -la D:/projects/glyph-arts/cli_charts/charts/
Expected: __init__.py 和 _utils.py 两个文件存在
```

### Check 2: Import 链通
```
Command: python -c "from cli_charts.charts._utils import _symbol_tier, _bar_symbols, _plt_finalize, _lttb, load_duckdb, _HiresCanvas, _catmull_pixels, _normalize_kline_dates, _statusline_values, _render_statusline, _capture_stdout, _has_flag, _rewrite_chat_argv, _rewrite_diagram_argv, _series_color, _canvas_line, _style_to_bar_symbols, _style_to_gauge, _textcharts_options, _sample_indices, _sample_data; print('all 20 helpers importable')"
Expected: stdout = "all 20 helpers importable", exit 0
```

### Check 3: 端到端 smoke (plotext runtime dep must be installed first)
**L1 报告 plotext 缺包导致 smoke 挂。plotext 是 runtime dep, 必须装上再跑。**

Step 3a: 装 plotext
```
Command: cd D:/projects/glyph-arts && uv pip install plotext 2>&1 | tail -5
Expected: "Installed" or "Already satisfied" 含 plotext
Result: PASS / FAIL
```
- 如果 `uv` 不在 PATH: 试 `python -m pip install plotext`
- 如果 3a 装失败 (network/编译错) → **FAIL, 阻塞**: 缺包不能当 pre-existing 跳过, runtime dep 是 venv 配置问题不是 L1 重构回归

Step 3b: smoke
```
Command: cd D:/projects/glyph-arts && python -c "from cli_charts.cli import main; main(['line','--json','[1,2,3,4,5]'])" 2>&1 | head -10
Expected: 非空 stdout, 包含 ASCII 折线 (退出码 0)
Result: PASS / FAIL
```

### Check 4: _helpers.py 缩了
```
Command: cd D:/projects/glyph-arts && git diff HEAD~1 -- cli_charts/cmd/_helpers.py | grep -c "^-[^-]"
Expected: ≥ 300 (净删除行数)
```

### Check 5: Shim 文件没被 L1 误动
```
Command: cd D:/projects/glyph-arts && git diff HEAD~1 --stat -- cli_charts/cmd/ | grep -v "_helpers.py\|parser.py\|media_args.py\|media_dispatch.py\|motion_commands.py\|text_input_commands.py\|direct_commands.py\|tool_commands.py\|animate_stream.py\|textcharts.py"
Expected: 0 行 (空输出 = shim 没动)
```

## 输出格式 (强制)
```
## Phase 1 / L2 Verifier Report

### Check 1: 文件结构
Command: <实际命令>
Output: <完整 stdout/stderr>
Result: PASS / FAIL

### Check 2: Import 链
... (同上格式)

### Check 3: smoke
... (同上格式)

### Check 4: _helpers.py 净减
... (同上格式)

### Check 5: shim 完整性
... (同上格式)

### Final Verdict: PASS / FAIL
### 如果 FAIL: 具体哪条 + 下一步 (回 L1 修哪个文件哪行)
```

## 决策规则
- 5 个 check 全 PASS → 写 "PASS, recommend merge"
- 任意 FAIL → 写 "FAIL, blocking: <具体>"，不写"looks fine but..."
- 任何 check 输出你没想到的内容 → FAIL + 报告 (不是 PASS + 备注)
