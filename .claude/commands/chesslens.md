---
description: 跑完整 ChessLens 流水线，为指定/最新对局生成小红书素材（封面+昏着卡），停在发布前等手动上传
argument-hint: "[game_id | chess.com 对局URL]（留空=最新一盘）"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill
---

为 chess 棋手 **aaronwang2026**（可被 `$CURRENT_CHESS_USER` 覆盖）跑完整 ChessLens 流水线，
产出小红书图文素材到 `output/{date}_{game_id}/post/`，**全程匿名打码、停在发布前**等用户手动上传。

参数 `$ARGUMENTS`：可为 game_id、chess.com 对局 URL，或留空（=取最新一盘）。

参照仓库内三个 skill 的 SKILL.md 执行（按文档驱动，不是 Skill 工具调用）：
[chess-game-history](../../skills/chess-game-history/SKILL.md) →
[chess-analysis](../../skills/chess-analysis/SKILL.md) →
[chess-xhs-post](../../skills/chess-xhs-post/SKILL.md)。

## 执行步骤

### 1. 解析目标对局
- 有 `$ARGUMENTS` → 解析出 game_id。
- 留空 → 从 chess.com API 取**最新一盘**。⚠️ 列表是**正序（最旧在前）**，必须用
  `max(games, key=lambda g: g["end_time"])`，**绝不能取 `games[0]`**。
  先查 `https://api.chess.com/pub/player/{user}/games/archives` 拿最新月份归档，
  最新月可能为空（月初）→ 回退上一个月。
- 取元数据：date、白/黑方、结果、time_control、ECO 开局名、game_id。

### 2. 缓存检查（命中则直接复用，跳过重复分析）
- 本地：`ls docs/reviews/docs/*{game_id}*`
- 数据：`ls -d data/*{game_id}*`
- 已有 `data/{date}_{game_id}/engine_eval.json` → 跳到第 5 步。

### 3. 取 PGN
- 首选 agent-browser（API PGN 有 20-30% 损坏率）；
  简单局可先用 API：`curl "https://api.chess.com/pub/player/{user}/games/{YYYY}/{MM}"` 里筛 game_id 取 `pgn`。
- 存到 `/tmp/game_pgn_{game_id}.pgn`。

### 4. 引擎分析（Stockfish）
```bash
python3 skills/chess-analysis/scripts/analyze.py \
  --pgn-file /tmp/game_pgn_{game_id}.pgn 16 \
  --focus-user aaronwang2026 \
  --output-dir data/{date}_{game_id}/
```
产出 `data/{date}_{game_id}/` 下 `pgn.json` / `engine_eval.json` / `metadata.json`。

### 5. ⚠️ 素材闸门（必须先判断再继续）
读 `engine_eval.json`：
- **`blunders` 列表为空（Aaron 这盘没失误，如 5 步速胜）** → **停下，不要硬凑昏着卡**，
  向用户报告并问方向：①改做「开局陷阱/速胜」教学帖 ②换一盘有失误的对局 ③用户指定 game_id。
- **有 blunders** → 继续第 6 步。

### 6. 渲染昏着对照棋盘图
```bash
python3 scripts/generate_blunder_images.py \
  --data-dir data/{date}_{game_id}/ \
  --output-dir output/{date}_{game_id}/images/xhs/ --top 3
```
脚本自动按 `eval_drop` 倒序、排除 `missed_wins`。**不要手写 FEN/步数/损失值。**

### 7. 按 chess-xhs-post 排版出图文
严格遵守 [chess-xhs-post](../../skills/chess-xhs-post/SKILL.md) 的**隐私铁律 + 失误排序规则**：
- 5 张图：`01_cover.png`（封面+**打码后的实战结果快照**+明确胜负横幅/印章）+
  `02/03/04_blunder_top{1,2,3}_*.png`（按 `eval_drop` 倒序）+ `05_missed_win_*.png`（有 `missed_wins` 才出）。
- 隐私：**禁**出现 `aaronwang2026`/对手账号/真名，一律「执白/执黑/对手」，footer 只写 `ChessLens`；
  结果截图按 SKILL 的 Step 4 用 PIL 打码（两条玩家信息条整条遮 + 裁左侧账号栏）。
- 着法用 `san` 原样；`missed_wins` 单独叙事不混入昏着卡。
- 昏着卡用 `ljg-card` 拼 HTML → `node ~/.claude/skills/ljg-card/assets/capture.js ... 1080 1440 fullpage` 截图。
- 写 `output/{date}_{game_id}/post/caption.txt`：标题钩子→背景悬念→TOP失误清单→错失速杀科普→升华→互动。
  话题标签 `#国际象棋 #棋局复盘 #chess #国象 #象棋复盘 #ChessLens`（**不带**账号标签）。
- 成品放 `output/{date}_{game_id}/post/`，镜像一份到 `images/xhs/`。

### 8. 小红书素材收尾（不发布）
**绝不自动发布。** 列出 `output/{date}_{game_id}/post/` 成品清单 + caption 预览，
告知用户「素材已就绪，手动上传」。如需半自动上传到小红书，再单独跑
`scripts/publish_xhs_agentbrowser.DEPRECATED.sh`（脚本也只停在发布前）。

### 9. 网站发布 + 验证（GitHub Pages）
小红书素材是一条线；复盘报告上 GitHub Pages 是另一条线（仓库 `wldandan/chessLens`，
站点 `https://wldandan.github.io/chessLens/`）。流程：
复盘 md（来自 `analyze.py`）→ 同步到 `docs/reviews/docs/` → `generate.py` 构建 `docs/*.html`
→ commit `docs/` → push main → `deploy.yml` 自动部署。

**先本地验证再 push，push 后再线上验证**（脚本已封装，任何一步红就停）：
```bash
# A. push 前：源就位检查 + 构建 + 断言新页/首页（确定性，零等待）
scripts/verify_publish.sh {game_id}
```
> ⚠️ 关键前置：`docs/reviews/docs/` 必须指向 `chess-reviews-summary` 的 md 源（含本局），
> 否则脚本会**拒绝构建**（防止把首页 index 清空再 push）。

本地全绿后，**让用户确认再 push**（不自动 push）：
```bash
git add docs/ && git commit -m "chore: add review for {game_id}"
git push origin main
# B. push 后：等 Actions 部署 + 线上 200/收录确认
scripts/verify_publish.sh {game_id} --remote
```
全绿 → 报告线上 URL `https://wldandan.github.io/chessLens/{date}_{game_id}_*.html`。
