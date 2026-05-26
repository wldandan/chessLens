---
name: chess-game-history
description: >
  获取指定棋手的历史对局记录。当用户说"查一下某人的对局"、
  "获取某账号的棋谱"、"某人在XX平台的历史战绩"、
  "帮我找某人的比赛记录"、"某玩家的对局列表"时触发此 skill。
  Also triggers when user provides a chess platform username and asks for their games.
---

# Chess Game History Fetcher

获取棋手的历史对局记录，并提取完整 PGN 供后续分析。

**默认用户**：若未指定用户名，则读取环境变量 `$CURRENT_CHESS_USER`；若环境变量也未设置，则默认 `aaronwang2026`。

## 目录结构

```
~/chessLens/chess-reviews-summary/
├── docs/          # 复盘分析 markdown 文件
├── images/       # chess.com 对局截图
└── videos/       # 生成的视频
```

**首次使用需创建 images 目录：**
```bash
mkdir -p ~/chessLens/chess-reviews-summary/images
```

## 平台支持

| Platform | API Base | Rate Limit |
|---|---|---|
| **Chess.com** | `https://api.chess.com/pub/player/{username}` | ~1000/day |
两者均有免费公开 API，无需 API key。

> ⚠️ **重要：Chess.com 对局列表按时间正序（最旧在前），永远不要直接取 `games[0]`！**
> API 返回的列表第一个是最旧的棋局，最新的在列表末尾。
> 正确做法：`latest_game = max(games, key=lambda g: g.get("end_time", 0))`

---

## 工作流程（检查本地缓存 → agent-browser 首选 → API 辅助）

### 第0步：检查本地缓存（优先）

获取棋手最新对局前，先检查本地是否已有分析记录：

```bash
ANALYSES_DIR="$HOME/chessLens/chess-reviews-summary/docs"

# 列出该棋手已有的分析文件
ls "$ANALYSES_DIR/"*_{username}_* 2>/dev/null
```

**判断逻辑：**
```
1. 从 API 获取目标对局基本信息（时间、对手、回合数）
2. 构造文件名：{日期}_{game_id}_{白方}_{胜负}_{黑方}_{回合数}步_{time_control}.md
   示例：2026-04-14_167293652644_aaronwang2026_执白胜_Clement924810_19步_10+0.md
   time_control 格式："10+0"（10分钟+0秒加成）或 "30+0"（30分钟慢棋）
3. 检查 $HOME/chessLens/chess-reviews-summary/docs/ 是否存在同名文件
4. 如已存在 → 直接读取本地文件输出，跳过所有获取
5. 如不存在 → 继续第1步
```

**重要：** 每次获取对局前必须先执行此检查，避免重复分析同一对局。

### 第0.5步：检查 GitHub docs 是否已有分析

本地没有时，进一步检查 GitHub 是否已有该对局分析：

```bash
GIT_DIR="$HOME/Projects/tutorials/chess-reviews-summary"
# 用 game_id 查找 GitHub docs 目录是否有该文件
ls "$GIT_DIR/docs/"*_{game_id}_* 2>/dev/null
```

**判断逻辑：**
```
1. 如果本地 docs/ 已存在 → 直接读取本地文件输出
2. 如果 GitHub docs/ 已存在 → 拉回本地后读取输出
3. 两个都没有 → 继续第1步获取 PGN 并分析
```

---

### 第1步：agent-browser 获取 PGN（首选）

**适用**：用户提供了 game ID 或游戏页面 URL，直接用浏览器获取 PGN，确保 100% 准确。

**用户提示：**
```
🔍 正在打开对局页面...
⏳ 正在加载棋谱...
🖱️ 正在提取 PGN...
✅ 获取完成，开始分析...
```

**操作步骤：**
```bash
# 打开游戏页面
agent-browser open "https://www.chess.com/game/live/{game_id}"
agent-browser wait --load networkidle

# 找到并点击 Share 按钮
agent-browser snapshot -i
# 根据 snapshot 输出找到 Share 按钮的 ref，点击它
agent-browser click @share_ref
agent-browser wait 1000

# 在弹出的 Share 面板中找到 PGN 按钮并点击
agent-browser snapshot -i
agent-browser click @pgn_button_ref
agent-browser wait 1000

# 获取 PGN 文本框内容
agent-browser snapshot -i
agent-browser get text @pgn_text_ref
```

**注意**：每次 snapshot 后 refs 会变化，必须在每次 click 前重新 snapshot。

**PGN 保存：**
```bash
# 将获取到的 PGN 保存到临时文件
echo "$PGN_TEXT" > /tmp/game_pgn_{game_id}.pgn
```

**PGN 截图（opencli 获取真实图片）：**
```bash
# 创建图片目录（如果不存在）
IMAGES_DIR="$HOME/chessLens/chess-reviews-summary/images"
mkdir -p "$IMAGES_DIR"

# 用 opencli 打开游戏页面并截图
opencli browser open "https://www.chess.com/game/live/{game_id}"
sleep 3  # 等待页面加载
opencli browser screenshot "$IMAGES_DIR/{game_id}.png"

# 在 markdown 中引用图片
# 在 ## 🏆 复盘总结 之后添加：
# ![对局截图](../images/{game_id}.png)
```

**注意**：
- opencli 复用已有 Chrome 会话，无需重新登录
- 截图包含完整棋盘和 Stockfish 分析
- 图片保存到 `~/chessLens/chess-reviews-summary/images/{game_id}.png`
- 在 markdown 顶部或底部添加图片引用：`![](../images/{game_id}.png)`

---

### 第2步：API 获取对局元数据（辅助）

**目的**：用 API 获取游戏的详细信息（日期、对手、回合数、时间控制），用于构造分析文件名。

```bash
# 如果有 game_id，直接获取该对局的元数据
curl "https://api.chess.com/pub/game/{game_id}"

# 或通过用户名和月份筛选（用户没给 game_id 时）
curl "https://api.chess.com/pub/player/{username}/games/{YYYY}/{MM}"
```

**用途**：
- 构造分析报告的文件名
- 获取 Opening 信息
- 验证对局基本信息（白方、黑方、结果）

---

### 第3步：分析 PGN

用 `analyze.py` 解析 PGN 并生成分析报告：

```bash
python3 ~/.agents/skills/chess-analysis/scripts/analyze.py --pgn-file /tmp/game_pgn_{game_id}.pgn 16
```

---

## 响应格式（列表展示）

```
📋 {Username} 的对局记录 — {Platform}

共获取 {N} 盘棋 | 胜 {W} / 平 {D} / 负 {L}

---
📅 {Date} | {TimeControl} | {Opening}
⚪ {WhitePlayer} ({Rating}) vs ⚫ {BlackPlayer} ({Rating})
结果：{Result}
🔗 {GameURL}
```

---

## 重要提示

- **PGN 获取优先用 agent-browser**：Chess.com API 返回的 PGN 有 20-30% 损坏率，直接用浏览器获取最可靠。
- **API 的作用是获取元数据**：日期、对手、评级、time control 等信息仍从 API 获取。
- **Game ID 获取**：用户没给 ID 时，用 API 按时间/月份筛选找到目标对局。

## 后续处理

PGN 获取完成后，交给 `chess-analysis` skill 进行详细分析：

```bash
# 调用 chess-analysis skill 的 analyze.py
python3 ~/.agents/skills/chess-analysis/scripts/analyze.py --pgn-file /tmp/game_pgn_{game_id}.pgn 16
```

**或**：直接调用 `chess-analysis` skill 进行完整复盘分析。
