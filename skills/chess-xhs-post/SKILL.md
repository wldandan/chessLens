---
name: chess-xhs-post
description: 为 ChessLens 赛后复盘生成小红书帖子图片素材（6张图排版）
version: '1.0.0'
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# ChessLens 小红书帖子生成 Skill

## 概述

自动为 ChessLens 赛后复盘生成小红书帖子，包含固定 6 张图排版。

## 6 张图排版

| 序号 | 位置 | 文件名 | 内容描述 |
|------|------|--------|----------|
| 1 | 开头/引入 | `xhs_02.jpg` | 金句："下棋不复盘，等于没下过" |
| 2 | 全局分析 | `xhs_01.jpg` | 完整对局复盘报告 |
| 3 | 失误 TOP1 | `blunder_card_top1.png` | 按 engine_eval.json `eval_drop` 倒序，丢分最大 |
| 4 | 失误 TOP2 | `blunder_card_top2.png` | 丢分第二 |
| 5 | 失误 TOP3 | `blunder_card_top3.png` | 丢分第三 |
| 6 | 结尾号召 | `xhs_00.jpg` + `xhs_cover.jpg` | 情感收尾 + ChessLens品牌宣传 |

## 关键规则

### 失误排序规则（非常重要）

**必须以 `data/{date}_{game_id}/engine_eval.json` 的 `blunders` 列表为准，按 `eval_drop` 倒序（丢分越大越靠前）**，不是文件名中的步数，也不是 xhs_01.jpg 的描述。

两条硬规则（踩过坑，务必遵守）：
1. **`missed_wins` 不要混入昏着卡**。`engine_eval.json` 里「错失速杀（原本可将杀但仍完胜）」单独放在 `missed_wins`，不是昏着，不上 TOP 卡（否则会出现「丢 992 分」这种被将杀哨兵值放大的误导标题）。
2. **着法记号用 `san` 字段原样**（如 `Ba6`，不是 `Bxa6+`）。

以 2026-05-24 对局（169159534058）为例，修正后的正确排序：
| 排序 | 步数 | 着法(san) | eval_drop | 应走 | 输出文件 |
|------|------|-----------|-----------|------|----------|
| TOP1 | 20 | Re3 | 7.28 | Qxf6 | `blunder_card_top1.png` |
| TOP2 | 13 | Qxd4 | 2.82 | Nxd4 | `blunder_card_top2.png` |
| TOP3 | 21 | Ra3 | 1.79 | Qf4 | `blunder_card_top3.png` |

> 注：第 37 步 Rb5+ 属 `missed_wins`（错失 Ra7+ 三步杀，但仍 +7.9 完胜），**单独叙事，不作昏着卡**。

### 配色

整体风格与 `xhs_00.jpg` 保持一致：
- 背景: `#F7F4EF` 浅米色
- 强调色: 红 `#DC2626`、绿 `#16A34A`、橙 `#D97706`
- 文字: 黑 `#111111`

## 执行流程

### Step 1: 准备素材目录

从对局 output 目录的 `images/xhs/` 中取用已有素材，或生成新的 blunder card。

目标目录结构：
```
output/{game_date}_{game_id}/images/xhs/
├── xhs_00.jpg
├── xhs_01.jpg
├── xhs_02.jpg
├── xhs_cover.jpg
├── blunder_card_top1.png
├── blunder_card_top2.png
└── blunder_card_top3.png
```

### Step 2: 从 engine_eval.json 提取 TOP-N 昏着

读取 `data/{game_date}_{game_id}/engine_eval.json`，对 `blunders` 按 `eval_drop` 倒序取前 3，每条记录：
- 步数 `move_no` + 走子方 `side`
- 错误着法 `san`
- 正确着法 `best_move`、`best_score`
- 丢分 `eval_drop`

`missed_wins` 单独取用（如需「错失速杀」叙事），**不并入 TOP 昏着**。
失误前局面 FEN = `pgn.json` 中上一手之后的 `fen`（即 ply `(move_no-1)*2 + (0白/1黑)` 的前一项）。

### Step 3: 生成 Blunder Card

如果需要生成新的 blunder card，执行以下步骤：

#### 3.1 渲染棋盘图（推荐：数据驱动脚本，自动取正确 TOP-N）

```bash
python3 scripts/generate_blunder_images.py \
  --data-dir data/2026-05-24_169159534058/ \
  --output-dir output/2026-05-24_169159534058/images/xhs/ --top 3
```

脚本直接读 `engine_eval.json`（按 `eval_drop` 倒序、自动排除 `missed_wins`）+ `pgn.json`（取失误前 FEN），
每个昏着输出一张上下对照棋盘图（红箭头=实走错着，绿箭头=最佳着）。**不要再手写 FEN/步数/损失值。**

如需手工渲染单张，用 `scripts/render_board.py` 的 `draw_board()`：

```python
import sys
sys.path.insert(0, 'scripts')
from render_board import draw_board
import chess

# 渲染错误着法（红色箭头）
img_wrong = draw_board(fen=FEN, arrows=[(from_sq, to_sq, (220, 60, 60))])
img_wrong.save('/tmp/blunder_N_wrong.png')

# 渲染正确着法（绿色箭头）
img_correct = draw_board(fen=FEN, arrows=[(from_sq, to_sq, (60, 200, 100))])
img_correct.save('/tmp/blunder_N_correct.png')
```

#### 3.2 拼装 Blunder Card HTML

用 `ljg-card` skill 生成，参考模板：

**配色变量**：
```css
:root {
  --bg: #F7F4EF;
  --green: #16A34A;
  --pink: #DC2626;
  --yellow: #D97706;
  --ink: #111111;
  --ink-light: #4B5563;
}
```

**布局**：左侧统计数据 + 右侧上下两个棋盘卡片

**HTML 结构**：
- Header: `关键失误 · TOP N`（橙色标签）
- 左侧列：`{步数}`大字 + 错误着法（红）+ 正确着法（绿）+ 损失值
- 右侧列：两个 board-card（错误/正确棋盘图）
- 底部：翠绿解释框 + `Powered by ChessLens AI`

#### 3.3 截图生成 PNG

```bash
cd ~/.claude/skills/ljg-card
node assets/capture.js /tmp/blunder_card_N.html /path/to/output/blunder_card_topX.png 1080 1440 fullpage
```

### Step 4: 输出到 xhs 目录

将 6 张图统一放到对局的 xhs 子目录：
```
output/{game_date}_{game_id}/images/xhs/
```

## 文案建议

**帖子标题**: `#国际象棋 #棋类复盘 #ChessLens #aaronwang2026`

**正文**:
复盘才能进步！今天这盘棋赢得很险...

---
*Powered by ChessLens AI*

## 数据来源（不要手写 FEN/损失值）

FEN、着法、损失值一律来自 `data/{date}_{game_id}/` 的 `engine_eval.json` + `pgn.json`，
由 `scripts/generate_blunder_images.py` 自动取用。手写硬编码是历史 bug 的来源（曾把
将杀哨兵值算成「丢 1007.90」、记号写成 `Bxa6+`、排序按步数而非丢分），已废弃。

2026-05-24 对局（169159534058）修正后 TOP3 昏着（来自 `engine_eval.json`）：

| 排序 | 步数 | 着法 | 应走 | eval_drop |
|------|------|------|------|-----------|
| TOP1 | 20 | Re3 | Qxf6 | 7.28 |
| TOP2 | 13 | Qxd4 | Nxd4 | 2.82 |
| TOP3 | 21 | Ra3 | Qf4 | 1.79 |

`missed_wins`：第 37 步 Rb5+（应走 Ra7+，三步杀），仍 +7.9 完胜——单独叙事，非昏着。