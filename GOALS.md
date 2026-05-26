# ChessLens 项目目标

**最后更新：** 2026-05-26
**负责人：** Leon Wang（爸爸） + Aaron Wang（14岁，aaronwang2026）

---

## 核心目标

**A. 棋力进步** — 帮助 Aaron 在 chess.com 上从 ~1450 进步
**B. 社媒建立** — 在小红书/X/视频号建立他的国际象棋内容账号

---

## 辅助目标

- 作为 2 年后接手的 portfolio 项目
- 作为 AI 培训教学案例

---

## 内容形态

### 图文帖（必须，每天）

| 类型 | 定位 |
|------|------|
| Infographic | 数据信息图（开局、失误、胜负手、评估曲线） |
| 风格 | Bloomberg/财新蓝，专业简洁 |

**工具：** mmx image（120次/天）+ 文字
**发布：** 小红书图文帖

### 长视频（辅助，每周 1-2 个）

**结构：**

```
mmx video 片头（6秒钩子）  ← 吸引用户
       ↓
FFmpeg 合成主体           ← 静态图 + TTS 旁白（不耗 video 额度）
  3-5 个关键局面图
       ↓
mmx video 片尾（6秒 CTA） ← 每天 4 次额度，1-2 个视频的片头尾
```

**工具：** mmx video（4次/天）、mmx speech、FFmpeg
**发布：** 小红书视频 / 视频号

---

## 发布渠道

| 平台 | 账号 | 内容 |
|------|------|------|
| 小红书 | Aaron 新号 | 图文帖 + 视频（主） |
| X/微博 | Aaron 新号 | 辅助 |
| 视频号 | 爸爸的号 | 视频 |

---

## 关键约束

- **不与 chess.com 竞争通用 UX**，聚焦差异化（复盘深度 + 社媒直出）
- **孩子主导内容创作**，爸爸做技术支撑
- 内容以 Aaron 为中心，记录他的进步
- 先跑通流程，再逐步让孩子参与更多

---

## 技术架构

### Phase 1：迁移（1-2周）

- Skills 已在 Hermes 全局目录（chess-analysis、chess-game-history、chess-player-stats）
- 新建 Hermes cron job（每天 7:00 UTC = 北京时间 15:00）
- 数据路径：`chess-reviews-summary/docs/`
- 验证 pipeline 不断裂

### Phase 2：内容适配层（2-3周）

- **content-adapter skill**：把复盘 Markdown → infographic 图片 + 视频素材包
- 输出：`output/YYYY-MM-DD_gameid/{scene_N.png, narration.wav, script.md, opening_prompt.txt, closing_prompt.txt}`
- 图文帖：mmx image → 小红书
- 视频：mmx video（片头尾） + FFmpeg 合成（主体） + TTS → 小红书/视频号

### Phase 3：孩子参与（持续）

- 让孩子看到自己频道的内容
- 让他选"哪盘想做视频"
- 逐步让他写文案、选封面
- 公开平台发布（小红书、视频号）

---

## 现状（OpenClaw → Hermes 迁移中）

- 现有复盘数据：20+ 对局在 `chess-reviews-summary/docs/`
- OpenClaw cron job ID：`1eee27ab-515e-453d-b750-bb0af1c63e50`（待迁移）
- Skills 已在全局：chess-analysis、chess-game-history、chess-player-stats