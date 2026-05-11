# Style-Based Rendering Redesign

> 目标：提升外部库利用率，从"一库一图"到"一图多风格"

## 1. 背景

### 1.1 当前痛点

glyph-arts 现有 52 种图表类型，但外部库利用率严重不均：

| 库 | 引用次数 | 利用率 | 问题 |
|----|---------|--------|------|
| plotext | 31 | 90%+ | 核心，但只用了 14/22 函数 |
| Rich | 多 | 中 | Layout/Progress/Markdown 等未用 |
| drawille | 2 | 100% | 已充分利用 |
| plotille | 2 | 5% | 仅 1 个图表类型 |
| uniplot | 1 | 5% | 仅 1 个图表类型 |
| textgraph | 2 | 中 | sparkline/hbar |
| art | 1 | 5% | 仅装饰 |
| networkx | 2 | 100% | graph 唯一用途 |
| textcharts | 新集成 | 60% | 9/15 类型已用 |

### 1.2 根本问题

**"一库一图"模式**：每个库只服务单一图表类型，缺少多风格组合：

```
当前:    line     ──→ plotext
        plotille ──→ plotille
        uniplot  ──→ uniplot

期望:    line ──┬→ plotext  (默认 fast)
                ├→ plotille (smooth)
                ├→ tplot    (braille)
                └→ uniplot  (scientific)
```

## 2. 设计目标

### 2.1 核心原则

1. **一图多风格**：同一图表类型支持多种渲染引擎
2. **风格继承**：用户可全局指定 `--style`，所有适用图表自动应用
3. **能力组合**：让小库（uniplot/plotille/textgraph）有多个使用场景
4. **向后兼容**：现有命令行为不变，新功能通过 `--style` 增量启用

### 2.2 量化目标

- plotille 利用率: 5% → 30%（应用到 line/scatter/curve）
- uniplot 利用率: 5% → 25%（应用到 line/scatter/hist）
- textgraph 利用率: 中 → 高（应用到 hbar/sparkline/bullet）
- Rich 利用率: 中 → 高（新增 progress/markdown/layout 命令）
- plotext: 启用 stem/error/themes 等未用功能

## 3. 架构设计

### 3.1 渲染风格分层

```
                  ┌──────────────────┐
                  │   User Input     │
                  │  type + --style  │
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │  Style Router    │
                  │  (registry.py)   │
                  └────────┬─────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   ┌─────────┐       ┌─────────┐         ┌─────────┐
   │  fast   │       │ smooth  │         │  rich   │
   │(plotext)│       │(plotille│         │ (Rich)  │
   │         │       │ /tplot) │         │         │
   └─────────┘       └─────────┘         └─────────┘

        ▼                  ▼                  ▼
   ┌─────────┐       ┌─────────┐         ┌─────────┐
   │   art   │       │  rgb    │         │ science │
   │(figlet/ │       │(drawille│         │(uniplot)│
   │  art)   │       │ + RGB)  │         │         │
   └─────────┘       └─────────┘         └─────────┘
```

### 3.2 风格定义

每种风格对应一种视觉体验：

| Style | 引擎 | 特点 | 适用图表 |
|-------|------|------|---------|
| `fast` | plotext | 默认，快速，紧凑 | line, scatter, bar, hist, kline |
| `smooth` | plotille | Braille 平滑曲线 | line, scatter, curve |
| `science` | uniplot | 科学记号轴标签 | line, scatter, hist |
| `rgb` | drawille (RGB) | 24-bit Braille | curve, line, scatter |
| `clean` | textcharts | 极简带 ANSI 颜色 | bar, hist, summary |
| `retro` | textgraph | 复古 sparkline 风格 | sparkline, hbar |
| `rich` | Rich | 表格/面板/边框 | table, panel, dashboard |

### 3.3 命令行 API

#### 3.3.1 现有方式（保持不变）

```bash
glyph-arts line --json '[{"label":"A","y":[1,2,3]}]'  # → plotext (默认 fast)
glyph-arts plotille --json '...'                       # → plotille (现有命令)
```

#### 3.3.2 新增 --style 参数

```bash
glyph-arts line --json '...' --style fast      # plotext (= 现状)
glyph-arts line --json '...' --style smooth    # plotille
glyph-arts line --json '...' --style science   # uniplot
glyph-arts line --json '...' --style rgb       # drawille RGB

glyph-arts bar --json '...' --style clean      # textcharts
glyph-arts bar --json '...' --style retro      # textgraph
```

#### 3.3.3 全局环境变量

```bash
export GLYPH_ARTS_STYLE=smooth
glyph-arts line --json '...'  # 自动 smooth
```

#### 3.3.4 兼容性

旧命令保留：`plotille`, `uniplot` 这些命令仍可用，作为风格的快捷方式。

```bash
glyph-arts plotille --json '...'  # 等价于 glyph-arts line --style smooth
glyph-arts uniplot --json '...'   # 等价于 glyph-arts line --style science
```

## 4. 新增命令（提升 Rich/plotext 利用率）

### 4.1 Rich 新命令

| 命令 | 库功能 | JSON Schema |
|------|--------|-------------|
| `progress` | `rich.progress.Progress` | `{"tasks":[{"name":"Build","total":100,"completed":75}]}` |
| `markdown` | `rich.markdown.Markdown` | `{"content":"# Title\n..."}` |
| `columns` | `rich.columns.Columns` | `{"items":["A","B","C"]}` |
| `rule` | `rich.rule.Rule` | `{"title":"section","style":"red"}` |
| `align` | `rich.align.Align` | `{"content":"text","align":"center"}` |

### 4.2 plotext 新命令

| 命令 | 库功能 | JSON Schema |
|------|--------|-------------|
| `stem` | `plt.stem()` | `{"x":[...],"y":[...]}` (茎叶图) |
| `error-bar` | `plt.error()` | `{"x":[...],"y":[...],"err":[...]}` |
| `matrix` | `plt.matrix_plot()` | `{"matrix":[[]]}` (矩阵图) |
| `shade` | `plt.shade()` | `{"x":[...],"y":[...],"shade":true}` |

### 4.3 textcharts 新命令（未用类型）

| 命令 | 类型 | 说明 |
|------|------|------|
| `histogram-tc` | `Histogram` | textcharts 直方图（与 plotext 的 hist 互补） |
| `line-tc` | `LineChart` | textcharts 折线图（极简风格） |

## 5. 实施步骤

### Phase 1：基础设施（无破坏性）
- [x] 在 `registry.py` 添加 style 路由表
- [x] `argparse` 新增 `--style` 参数
- [x] 环境变量 `GLYPH_ARTS_STYLE` 支持
- [x] `--list-styles` 显示可用风格

### Phase 2：line/scatter 多风格
- [x] `line --style smooth` → tplot (plotille fallback)
- [x] `line --style science` → uniplot
- [x] `line --style rgb` → drawille + RGB (fallback when missing)
- [ ] `scatter --style smooth/science/rgb` (same routing, needs testing)
- [ ] 测试每种风格输出

### Phase 3：bar/sparkline 多风格
- [x] `bar --style clean` → textcharts BarChart
- [x] `bar --style retro` → textgraph
- [x] `sparkline --style retro` → textgraph 现有
- [ ] `sparkline --style fast` → sparklines

### Phase 4：Rich 新命令
- [ ] `progress` 命令
- [ ] `markdown` 命令
- [ ] `columns` 命令
- [ ] `rule` 命令

### Phase 5：plotext 新命令
- [ ] `stem` 命令
- [ ] `error-bar` 命令
- [ ] `matrix` 命令

### Phase 6：文档
- [ ] 更新 README.md
- [ ] 更新 SKILL.md
- [ ] 添加 demo gallery 截图
- [ ] CHANGELOG

## 6. 兼容性

### 6.1 向后兼容

- 所有现有命令保留（`plotille`/`uniplot` 标记 deprecated）
- 所有现有 JSON schema 保留
- `plotille` → 自动映射到 `line --style smooth`
- `uniplot` → 自动映射到 `line --style science`
- 默认行为不变（`--style` 不指定时用 plotext）
- 缺依赖时 WARN + fallback 到 plotext

### 6.2 渐进迁移

旧用户：不需要任何修改  
新用户：可选用 `--style` 探索更多风格

## 7. 风险与权衡

### 7.1 风险

- **复杂度增加**：用户需要理解 style 概念
- **测试矩阵爆炸**：M 个类型 × N 个风格 = M*N 测试
- **依赖膨胀**：所有风格库都需要安装

### 7.2 缓解方案

- **可选依赖**：每个风格库列为 optional-dependencies
- **降级提示**：缺失依赖时给出明确安装指令
- **核心测试**：每个 (类型, 风格) 组合至少 1 个 smoke test

### 7.3 不引入的库

- **mpl-ascii**: 与 plotext 重复，不集成
- **terminal-stonks**: 依赖 pandas DatetimeIndex，门槛高，不集成

## 8. 成功指标

- 实施完成后，外部库利用率均衡：
  - plotille: 5% → 30%
  - uniplot: 5% → 25%
  - textgraph: 中 → 高
  - Rich: 中 → 高
- 新增 ~10 个命令（不破坏现有）
- 总图表类型: 52 → 60+
- 所有 148+ 测试通过

## 9. 时间估算

| Phase | 工作量 | 优先级 |
|-------|--------|--------|
| Phase 1 | 0.5 天 | P0 |
| Phase 2 | 1 天 | P0 |
| Phase 3 | 0.5 天 | P1 |
| Phase 4 | 1 天 | P1 |
| Phase 5 | 0.5 天 | P2 |
| Phase 6 | 0.5 天 | P0 |

**总计**：约 4 天

## 10. 决策记录 (2026-05-11)

### Q1: `--style` vs `--engine` → 保持分离

- `--engine` 决定输出介质（pixel=PNG, ascii=终端文本）
- `--style` 决定渲染风格（fast/smooth/science/rgb/clean/retro/rich）
- 组合灵活，后续增加新风格库简单

### Q2: plotille/uniplot 独立命令 → deprecated + 自动映射

- 标记 deprecated，保留兼容层
- 自动映射：`plotille` → `line --style smooth`，`uniplot` → `line --style science`
- 旧脚本可用，新脚本统一风格接口

### Q3: 缺依赖行为 → WARN + fallback

- 默认：WARN 提示 + 静默降级到 plotext
- 严格模式：`--strict-style` 报错 `ERROR:dep:`
- 不需要 `--ignore-missing`（默认就是降级）

### Q4: tplot vs plotille → tplot 为 smooth 核心，plotille 为 fast fallback

- `--style smooth` 核心引擎：**tplot**（Braille 平滑效果最佳）
- `--style fast` / fallback：**plotille**（轻量）
- plotext 处理复杂图表（error bar, histogram, kline）

### 最终分层

```
smooth  → tplot (Braille 平滑曲线)
fast    → plotext (默认) / plotille (fallback)
science → uniplot (科学记号)
rgb     → drawille (24-bit Braille)
clean   → textcharts (极简 ANSI)
retro   → textgraph (复古 Unicode)
rich    → Rich (表格/面板/进度)
art     → figlet + art (艺术字)
```

