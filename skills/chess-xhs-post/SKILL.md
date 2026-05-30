---
name: chess-xhs-post
description: 为 ChessLens 赛后复盘生成小红书帖子图片素材（封面+昏着卡+错失速杀+结果原图）。棋手为未成年人，全程匿名（不露 chess.com 账号/真名，结果截图打码）。
version: '1.2.0'
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

自动为 ChessLens 赛后复盘生成小红书帖子。标准排版 5 张图：封面（合并打码实战战绩）+ 三张昏着卡 + 错失速杀卡。

## 图片排版（封面 + 3 昏着 + 错失速杀 + 结果原图）

| 序号 | 位置 | 文件名 | 内容描述 |
|------|------|--------|----------|
| 1 | 封面（合并战绩）| `01_cover.png` | 标题钩子 + **嵌入打码的 chess.com 实战快照**（带「执白胜 1-0」横幅/印章）+ 底部悬念。首图即钩子+战绩证明，匿名 |
| 2 | 失误 TOP1 | `02_blunder_top1_*.png` | 按 engine_eval.json `eval_drop` 倒序，丢分最大 |
| 3 | 失误 TOP2 | `03_blunder_top2_*.png` | 丢分第二 |
| 4 | 失误 TOP3 | `04_blunder_top3_*.png` | 丢分第三 |
| 5 | 错失速杀 | `05_missed_win_*.png` | 取自 `missed_wins`，紫色卡，**单独叙事，非昏着**（无则省略）|

> **封面合并战绩**：把打码后的 chess.com 实战快照嵌进封面中段（避免封面留白、首图即给社会证明），
> 比"封面 + 单独结果图"两张分开更紧凑、冲击力更强。实战图处理见 Step 4，胜负要**明确标注**
> （绿色横幅「执白胜 · 对手弃局 1-0」+「1-0 白胜」印章）——因为 chess.com 的 *game abandoned* 画面本身看不出谁赢。
> 文件名带 `*` 处填步数+着法（如 `02_blunder_top1_m20_Re3.png`），便于核对。
> 输出统一放 `output/{date}_{game_id}/post/` + `images/xhs/`，配文 `post/caption.txt`。

## 🔒 隐私与匿名规则（铁律，针对未成年棋手）

棋手 Aaron 为未成年人，**所有对外素材一律匿名**，违反即返工：

1. **不露任何 chess.com 账号**：封面/卡片不写 `aaronwang2026`、对手 `itsbishara` 等用户名，
   一律用「执白 / 执黑 / 对手」代称。对局信息只保留开局名、结果、日期。
2. **不露真名**：卡片署名/footer 只用品牌 **`ChessLens`**，**不要**出现「Aaron」「Aaron 的棋」等真实名字。
3. **文案标签同步**：`caption.txt` 不带 `#aaronwang2026` 之类账号标签；正文不点名双方账号。
4. **chess.com 结果原图必须打码**：截图自带双方头像 + 用户名 + 评分 + 左侧登录账号，
   直接用会泄露身份。处理步骤见下方「Step 4: 结果原图匿名化」，
   要点：**裁掉左侧账号栏 + 上下两条玩家信息条整条打码（头像/用户名/国旗/评分全遮）**。

> 口诀：**对外只认 ChessLens，不认人。** 品牌靠 IP，不靠真名。

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

从对局 output 目录取用棋盘图，或用 `generate_blunder_images.py` 重新生成。

目标目录结构（成品 + 配文）：
```
output/{game_date}_{game_id}/
├── post/                          # 发布用，按序号排好
│   ├── 01_cover.png               # 封面 + 嵌入打码实战快照（执白胜 1-0）
│   ├── 02_blunder_top1_*.png
│   ├── 03_blunder_top2_*.png
│   ├── 04_blunder_top3_*.png
│   ├── 05_missed_win_*.png        # 有 missed_wins 才出
│   └── caption.txt
└── images/xhs/                    # 镜像一份
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
- 底部：footer 署名只用 **`ChessLens`**（**禁**出现真名「Aaron」/账号）

#### 3.3 截图生成 PNG

```bash
cd ~/.claude/skills/ljg-card
node assets/capture.js /tmp/blunder_card_N.html /path/to/output/blunder_card_topX.png 1080 1440 fullpage
```

### Step 4: 结果原图匿名化（chess.com 截图）

chess.com 对局结束截图（如 `images/board.png`）自带**双方头像 + 用户名 + 评分 + 左侧登录账号**，
**绝不能原样发布**。用 PIL 处理后再包成品牌结果卡：

```python
from PIL import Image, ImageFilter, ImageDraw
im = Image.open("images/board.png").convert("RGB")  # 例：1280x757
def redact(box):                                     # 模糊+实色遮盖，文字彻底消失
    im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(12)), box[:2])
    ImageDraw.Draw(im).rectangle(box, fill=(38, 36, 33))  # 匹配 chess.com 深色背景
redact((232, 0,   772, 48))    # 顶部玩家信息条：头像/用户名/国旗/评分 整条遮
redact((232, 596, 772, 650))   # 底部玩家信息条：同上
im.crop((232, 0, 772, 652)).save("/tmp/result_clean.png")  # 裁掉左侧登录账号栏 + 右侧广告
```

> 坐标按截图分辨率微调；核心是**两条玩家条整条打码 + 裁掉左侧账号栏**，
> 保留棋盘 + "game abandoned/checkmate" 弹窗即可。
>
> **打码后的快照嵌入封面（01_cover）中段**：用 HTML 叠层加绿色横幅「🏆 执白胜 · 对手弃局 1-0」+
> 右下「1-0 白胜」印章——因为 chess.com 的 *game abandoned* 画面本身看不出谁赢，**必须显式标注胜负**。
> 卡内文字一律用「执白 / 执黑 / 对手」，footer 只写 `ChessLens`。
> （中文叠字用 HTML/CSS，**不要**用 PIL 画中文——PIL 默认字体不支持中文会报 latin-1 编码错。）

### Step 5: 输出到 post / xhs 目录

将成品图按 `01_cover` → `06_result` 顺序放入 `output/{date}_{game_id}/post/`，
同时镜像一份到 `images/xhs/`，并写 `post/caption.txt`。

### Step 6: 发布到小红书（agent-browser 半自动）

用 `scripts/publish_xhs.sh` 把 `post/` 整套发到小红书创作服务平台：

```bash
scripts/publish_xhs.sh output/{date}_{game_id}/post/
```

脚本会：登录态检查 → 切「上传图文」→ 按序号上传 `NN_*.png` → 填标题(caption 第1行)
+ 正文(第3行起，含话题标签) → 截图留证，**停在「发布」前**（绝不自动点发布，由人确认）。

**agent-browser 发布踩坑（务必记住，已固化进脚本）**：

1. **独立浏览器实例**：agent-browser 不是用户日常的 Chrome，需**自己登录一次**。
   用固定 `--session-name xhs` 持久化登录态；未登录时脚本会开有头浏览器让你扫码/验证码登录，
   登录后重跑即可。`--auto-connect` 接管用户 Chrome 常报 401，不可靠。
2. **上传文件别用 `@ref`**：切 tab / DOM 变动后 ref 立即失效，报
   `CDP error (DOM.describeNode): Object id doesn't reference a Node`。
   **直接用 CSS 选择器 `input[type=file]` 上传**才稳：
   `agent-browser --session-name xhs upload "input[type=file]" 01.png 02.png ...`（一次可传多张，顺序即图序）。
3. **标题/正文框 ref 会变**：每次操作前重新 `snapshot -i` 取 ref。标题框占位符是「填写标题会有更多赞哦」；
   正文框是标题之后第一个无名 textbox（避开「添加地点/选择群聊」的嵌套 textbox）。
4. **铁律：永远停在发布前**。脚本不点最终「发布」，人工核对预览截图后再手动点。

## 文案建议（caption.txt）

**话题标签**: `#国际象棋 #棋局复盘 #chess #国象 #象棋复盘 #ChessLens`
（⚠️ **不带** `#aaronwang2026` 等账号标签；正文也不点名双方账号——见隐私铁律）

**正文结构**：标题钩子 → 一句话背景+悬念 → TOP 失误清单（数值对齐 engine_eval.json）
→ 错失速杀科普 → 价值升华（「下棋不复盘=没下过」）→ 互动提问。

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