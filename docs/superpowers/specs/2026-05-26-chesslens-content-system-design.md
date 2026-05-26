# ChessLens 内容发布系统 — 设计文档

**日期：** 2026-05-26
**方案：** 方案C — 半自动内容包 + 渐进参与

---

## 1. 目标回顾

- **核心：** 14岁孩子 Aaron (aaronwang2026) 棋力进步 + 建立社媒存在感
- **现有 pipeline：** 每天 7:00 UTC cron → Stockfish 分析 → 输出到 `docs/`
- **问题：** 孩子不看这些复盘，没有真正接触到内容

---

## 2. 方案C 架构

```
现有 pipeline（不动）
        ↓
  新增"内容适配层"（content-adapter）
        ↓
  生成"一键发布包"：
    ├── 图文帖（infographic 图片 + 文字）
    ├── 视频素材（自动生成的复盘解说视频）
    └── 文案草稿（可直接复制发送）
        ↓
  孩子：查看 → 审核 → 一键发布到社媒渠道
```

---

## 3. 核心组件

### 3.1 内容适配层（content-adapter）

**输入：** `docs/` 里的复盘 Markdown 文件

**输出：** `output/` 下的发布包

```
output/
├── YYYY-MM-DD_gameid/
│   ├── infographic.png      # 静态信息图（配文字）
│   ├── video.mp4             # 自动生成的复盘视频（字幕+画外音）
│   ├── caption.txt           # 一键复制文案（适合粘贴到Telegram/微信）
│   └── thumbnail.jpg          # 视频封面
```

### 3.2 图文帖生成（infographic）

- 数据来源：复盘 Markdown（开局、失误点、胜负手、评分走势）
- 工具：baoyu-imagine 或 matplotlib 脚本
- 风格参考：Bloomberg/财新蓝，数据信息图风格
- 尺寸：小红书 3:4，朋友圈 1:1，Telegram 16:9

### 3.3 视频生成

- 数据来源：复盘 Markdown + Stockfish 评估
- 工具：baoyu-slide-deck → FFmpeg 合成，或现有 analyze.py 扩展
- 格式：MP4，带字幕，3-5分钟，有叙事逻辑（开局→中局→收尾）
- 音轨：文字转语音（TTS）配解说

### 3.4 频道/发布渠道

**内容发布（图文/视频）：**
- **小红书** — 主要平台，图文帖 + 长视频
- **微博/X** — 辅助平台
- **视频号** — 用爸爸自己的账号发布视频

**注：不发微信公众号（该账号另有用处）**

**当前已有能力：**
- baoyu-post-to-xiaohongshu skill 已配置
- baoyu-post-to-weibo skill 已配置
- baoyu-post-to-x skill 已配置
- 视频号发布：待接入

---

## 4. 迁移计划：从 OpenClaw 到 Hermes

### 4.1 现状（OpenClaw）

```
7:00 UTC cron → chess-ai-coach agent
  → Stockfish depth 16 分析
  → 输出 docs/*.md
```

- agent 在 OpenClaw 环境运行
- skills：`chess-analysis`, `chess-game-history`, `chess-player-stats`
- 结果：纯 Markdown 文件，人类不友好

### 4.2 迁移到 Hermes

**Skill 复用：**
- skills 目录一致（`~/.agents/skills/`），可直接复制到 `~/.hermes/skills/`
- chess-analysis / chess-game-history / chess-player-stats 三个 skill 迁移

**新 Skill：content-adapter**
- 新开发，负责把 Markdown 复盘转换成发布包
- 用 baoyu-imagine 生成图片
- 用 TTS 生成视频配音

**Cron job 迁移：**
- 把 OpenClaw cron job 迁移到 Hermes cron job
- 同样每天 7:00 UTC 触发

**数据流：**

```
Hermes cron (7:00 UTC)
  → chess-ai-coach skill（分析对局）
  → content-adapter skill（生成发布包）
  → 小红书图文帖（baoyu-post-to-xiaohongshu）
  → 视频号（baoyu-post-to-video，future）
```

---

## 5. 实施步骤

### Phase 1：迁移 + 跑通（1-2周）

- [ ] 迁移 skills 到 Hermes
- [ ] 复制现有 cron job 到 Hermes
- [ ] 验证 pipeline 不断裂
- [ ] Telegram 测试频道建立

### Phase 2：内容适配层开发（2-3周）

- [ ] content-adapter skill 开发
- [ ] infographic 生成脚本
- [ ] 视频生成脚本（TTS + 字幕）
- [ ] 输出格式适配各平台

### Phase 3：孩子参与（持续）

- [ ] 让孩子看到自己频道的内容
- [ ] 让他选"哪盘想做视频"
- [ ] 逐步让他自己写文案
- [ ] 公开平台发布（小红书/视频号）

---

## 6. 权衡

| | 方案A（完全自动） | 方案C（半自动） | 方案B（交互App） |
|--|--|--|--|
| 孩子参与度 | 低 | 中→高 | 高 |
| 开发量 | 低 | 中 | 高 |
| 风险 | 孩子变成发布员 | 需要引导 | 开发周期长 |
| 适合 | 纯技术验证 | **推荐** | 有明确需求时 |

---

## 7. 下一步

等待用户批准后：
1. 迁移 skills 到 Hermes
2. 在 Hermes 建立 cron job
3. 建立 Telegram 测试频道