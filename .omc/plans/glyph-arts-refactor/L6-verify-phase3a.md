# L6 — Phase 3a Verifier (independent context)

## 目的
独立验证 L5 的 Phase 3a 落地 + 确认 lead 0685159 hotfix 落地正确。
**L5 自报 18/19 smoke PASS + CMDS=72, 但 lead 复测发现 L5 用了 `from x import y` 形式搬函数, 导致 @register 装饰器不触发, cli_charts.registry.CMDS 从 44 掉到 32。** Lead hotfix 0685159 已经把 19 个 @register 装饰器补回去, CMDS 恢复到 51。你的任务:
1. 确认 hotfix 真的补对了 (无 over-patch, 无 under-patch, 无副作用)
2. 确认 19 个函数体 byte-identical pre/post refactor
3. 独立决定这是 PASS 还是 FAIL。

## Cold start 加载
1. Read `D:/projects/glyph-arts/.omc/plans/glyph-arts-refactor/L5-impl-phase3a.md` (规格)
2. Read `D:/projects/glyph-arts/.omc/plans/glyph-arts-refactor/STATUS.md` (L5 commit SHA + hotfix 0685159)
3. Read `D:/projects/glyph-arts/cli_charts/registry.py` 了解 `@register` 装饰器怎么写
4. Read `D:/projects/glyph-arts/_hotfix_registers.py` 了解 hotfix 怎么改的
5. **不要** 读 L5 的 chat log, 不要继承 L5 的假设
6. **不要** 读 hotfix 之后的 chat log, 独立复测

## 角色约束
- 你是 verifier, **不允许 Edit/Write/Notebook** (无写入工具, 物理禁止)
- 你的 PASS/FAIL 报告 = L5 能不能 merge 的最终判决
- 没跑命令的 PASS = skip, 不算 PASS

## 验证清单 (7 checks, 全部要有 Command + Output + Result)

### Check 1: 19 个新文件存在
```
Command: cd /d/projects/glyph-arts && ls cli_charts/charts/aggregates/ cli_charts/charts/composite/ cli_charts/charts/algebra/
Expected: 10 + 3 + 6 = 19 .py 文件
Result: PASS / FAIL (列出实际数)
```

### Check 2: 19 个新文件可独立 import
```
Command: cd /d/projects/glyph-arts && .venv\Scripts\python.exe -c "
import importlib.util, os, glob
for d in ['aggregates','composite','algebra']:
    for f in sorted(glob.glob(f'cli_charts/charts/{d}/*.py')):
        spec = importlib.util.spec_from_file_location(os.path.basename(f)[:-3], f)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        print(f'OK {f}')
"
Expected: 19 行 "OK ..."
Result: PASS / FAIL
```

### Check 3: _helpers.py 不再含 19 个函数体
```
Command: cd /d/projects/glyph-arts && for fn in graph comparison diverging summary sparkline_table cdf_chart rank_table percentile boxplot_comparison stacked_bar_text panel dashboard rich_live formula formula_pretty calibrate status_command splash_command wave_command; do count=$(grep -c "^def $fn(" cli_charts/cmd/_helpers.py); echo "$count $fn"; done
Expected: 全部 count = 0
Result: PASS / FAIL (列出 count > 0 的)
```

### Check 4: 19 个函数体字节级未动 (跟 commit 0685159^ = hotfix 前 = L5 final state 对比)
**L5 spec: "函数体 0 修改, 签名 0 修改"**
Hotfix 0685159 在每个新文件加了 `@register("name")` 装饰器 + `from cli_charts.registry import register` import + 1 个空行 (共 3 行)。函数体本身未动。

方法 A — 用 git show 拉 hotfix 前的文件, 跳过前 3 行 (import + decorator + blank), 跟当前文件跳过同样 3 行 diff 函数体:
```
Command: cd /d/projects/glyph-arts
# 拉 hotfix 前的版本 (hotfix 0685159^ = L5 final state)
git show 0685159^:cli_charts/cmd/_helpers.py > /tmp/before_helpers.py

for d in aggregates composite algebra; do
  for f in cli_charts/charts/$d/*.py; do
    name=$(basename $f .py)
    # 提取 before_helpers.py 里 def name(...) 起的函数体
    # 简单做法: 用 sed 找 def 行号, 然后 awk 提取到下一个顶层 def/class 为止
    defline=$(grep -n "^def $name(" /tmp/before_helpers.py | head -1 | cut -d: -f1)
    if [ -z "$defline" ]; then echo "MISSING $name (in before)"; continue; fi
    # 用 awk 跳过空行, 提取函数体
    awk -v start=$defline 'NR>=start && /^(def |class )/ && NR>start {exit} NR>=start' /tmp/before_helpers.py > /tmp/before_fn.py
    # 现在新文件: @register 装饰器 + 空行 + def
    # 跳过装饰器和空行, 找 def 行
    defline2=$(grep -n "^def $name(" "$f" | head -1 | cut -d: -f1)
    awk -v start=$defline2 'NR>=start && /^(def |class )/ && NR>start {exit} NR>=start' "$f" > /tmp/after_fn.py
    if diff -q /tmp/before_fn.py /tmp/after_fn.py > /dev/null; then
      echo "MATCH $name"
    else
      echo "DIFF $name"
      diff /tmp/before_fn.py /tmp/after_fn.py | head -20
    fi
  done
done
Expected: 19 行 MATCH, 0 行 DIFF
Result: PASS / FAIL (列差异文件)
```

**Fallback** (如果上面 awk 复杂): 用 git diff 直接看 0685159^ 跟 0685159 的差异, 应该只显示每个文件 +3 行 (import + @register + blank), 函数体应完全相同:
```
Command: cd /d/projects/glyph-arts && git diff 0685159^ 0685159 -- 'cli_charts/charts/aggregates/' 'cli_charts/charts/composite/' 'cli_charts/charts/algebra/' | grep -E '^[+-]' | grep -vE '^(---|\+\+\+|@@)' | sort | uniq -c | sort -rn | head -20
Expected: 大量 + 行 (装饰器+import+blank), 极少 - 行 (因为 hotfix 是 additive), 函数体内部行不应有 +/- 配对出现
Result: PASS / FAIL
```

### Check 5: registry CMDS count (post-hotfix 0685159)
**L5 报"CMDS=72" — lead 复测发现 L5 测错对象了 (测的是 _helpers.CMDS 不是 cli_charts.registry.CMDS), 实际 L5 final state = 32 (掉 12: 9 L5-displaced + 3 装饰器没触发的复合函数)。Lead hotfix 0685159 补回 19 个 @register, 期望 CMDS = 51。**

```
Command: cd /d/projects/glyph-arts && .venv\Scripts\python.exe -c "
from cli_charts.cmd import bootstrap
bootstrap()
from cli_charts.registry import CMDS
print('cli_charts.registry.CMDS count:', len(CMDS))
# 还应该检查 19 个新模块名字全部 in CMDS
expected = ['graph','comparison','diverging','summary','sparkline_table','cdf_chart','rank_table','percentile','boxplot_comparison','stacked_bar_text','panel','dashboard','rich_live','formula','formula_pretty','calibrate','status_command','splash_command','wave_command']
missing = [n for n in expected if n not in CMDS]
print('missing:', missing if missing else 'none')
# 还应该检查每个都是 callable
non_callable = [n for n, v in CMDS.items() if not callable(v)]
print('non_callable:', non_callable if non_callable else 'none')
"
Expected: count=51, missing=none, non_callable=none
Result: PASS / FAIL
```

**判定标准**:
- count == 51 + missing == none + non_callable == none → PASS (hotfix 正确)
- count ∈ [44, 50] → 缺几个, 标 "PARTIAL: hotfix 补了大部分, 但漏 N 个, follow-up 补"
- count < 44 → hotfix 没补对, FAIL blocking

### Check 5b: 19 个文件每个都真有 @register 装饰器 (静态检查)
防止 hotfix 只补了部分文件 (例如只补了 aggregates 没补 composite/algebra)
```
Command: cd /d/projects/glyph-arts && for d in aggregates composite algebra; do
  for f in cli_charts/charts/$d/*.py; do
    name=$(basename $f .py)
    if grep -q "^@register(\"$name\")" "$f"; then
      if grep -q "from cli_charts.registry import register" "$f"; then
        echo "OK $f"
      else
        echo "MISSING-IMPORT $f (decorator yes, import no)"
      fi
    else
      echo "MISSING-DECORATOR $f"
    fi
  done
done
Expected: 19 行 OK, 0 行 MISSING-*
Result: PASS / FAIL

### Check 6: 端到端 19 个 smoke (跟 L5 spec schema 一样)
```
Command: cd /d/projects/glyph-arts && .venv\Scripts\python.exe -c "
from cli_charts.cli import main
cmds = ['graph','comparison','diverging','summary','sparkline_table','cdf_chart','rank_table','percentile','boxplot_comparison','stacked_bar_text','panel','dashboard','rich_live','formula','calibrate','status','splash','wave','formula_pretty']
results = []
for t in cmds:
    try:
        main([t,'--json','{\"y\":[1,2,3,4,5]}'])
        results.append((t, 0))
    except SystemExit as e:
        results.append((t, e.code if e.code is not None else 0))
    except Exception as e:
        results.append((t, f'{type(e).__name__}: {e}'))
for t, r in results: print(f'{t}: {r}')
"
Expected: 18/19 exit 0; 1 (wave) may fail on wsh FileNotFoundError (env dep, accept as P1 gap)
Result: PASS / FAIL (列出失败命令 + 原因)
```

### Check 7: shim 文件没被 L5 误动
```
Command: cd /d/projects/glyph-arts && git diff edd9b7b^ edd9b7b --stat -- 'cli_charts/cmd/*.py' | grep -v "_helpers.py\|__init__.py"
Expected: 空 (只有 _helpers.py 和 __init__.py 改, shim 没动)
Result: PASS / FAIL (列出被改的 shim 文件)
```

## 输出格式 (强制)
```
## Phase 3a / L6 Verifier Report

### Check 1: 19 个新文件存在
Command: ...
Output: ...
Result: PASS / FAIL

### Check 2: ...
... (全部 8 个: 1, 2, 3, 4, 5, 5b, 6, 7)

### Check 5 深度分析 (lead 重点)
- L5 报: cli_charts.registry.CMDS = 72 (误测)
- L5 final 实际: cli_charts.registry.CMDS = 32 (掉 12, 根因: `from x import y` 不触发 @register)
- Lead hotfix 0685159 后: cli_charts.registry.CMDS = 51
- 你独立测得: <你的数字>
- hotfix 是否正确: <是/否, 证据: 19 个名字都在, 0 个 non_callable, count=51>
- 19 个文件装饰器静态检查: <OK x19 / MISSING x N>

### Check 4 函数体 byte-identical 深度分析
- 比较对象: 0685159^ (L5 final) 跟 0685159 (hotfix)
- 预期: 每个文件 +3 行 (import + decorator + blank), 函数体本身 byte-identical
- 实际: <19 MATCH / N DIFF>
- 任何函数体 DIFF: <列文件名, 列首 20 行 diff>

### Final Verdict: PASS / FAIL
### 如果 FAIL: 具体哪条 + 下一步 (回 hotfix/L5 修哪个文件哪行)
```

## 决策规则
- 全部 8 个 check PASS → 写 "PASS, recommend merge Phase 3a"
- 任意 FAIL → 写 "FAIL, blocking: <具体>"
- 任何 check 输出你没想到的内容 → FAIL + 报告 (不是 PASS + 备注)
- Check 5/5b 是 lead 重点关注的差异点, 务必独立复测, 不接受 L5 报告的数字

## 决策规则
- 7 个 check 全 PASS → 写 "PASS, recommend merge"
- 任意 FAIL → 写 "FAIL, blocking: <具体>"，不写"looks fine but..."
- 任何 check 输出你没想到的内容 → FAIL + 报告 (不是 PASS + 备注)
- Check 5 是 lead 重点关注的差异点, 务必给出根因诊断 (是不是 L5 regression)
