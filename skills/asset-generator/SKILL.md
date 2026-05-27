---
name: asset-generator
description: >
  将 chess-analysis 输出的 JSON 数据转换为内容发布包。
  输入 data/{date}_{game_id}/ 目录，输出 output/{date}_{game_id}/ 包含 review.md、data.json、highlights.md 和 images/。
  当用户说"生成发布内容"、"制作复盘素材"、"这盘棋做图文"时触发。
---

# asset-generator Skill

读取 `data/{game_id}/` 下的 JSON 文件，生成可发布的复盘内容。

## 依赖

- 依赖 `chess-analysis` skill 先运行，生成 `data/{game_id}/` 下的 JSON 文件
- 数据流程：chess-analysis → data/ → asset-generator → output/ → 发布平台

## 输入数据格式

```
data/{date}_{game_id}/
├── metadata.json    # 游戏元数据
├── engine_eval.json # Stockfish 评估
└── pgn.json         # 棋谱（可选）
```

## 输出

```
output/{date}_{game_id}/
├── review.md         # 教练式复盘文章
├── data.json         # 结构化数据（供 infographic 用）
├── highlights.md     # 社媒文案草稿
└── images/
    ├── board.png         # 棋盘截图
    ├── infographic_placeholder.txt
    └── thumbnail_placeholder.txt
```

## 子模块

| 模块 | 文件 | 职责 |
|------|------|------|
| review_writer | review_writer.py | 生成 review.md |
| data_extractor | data_extractor.py | 生成 data.json |
| social_copywriter | social_copywriter.py | 生成 highlights.md |
| image_generator | image_generator.py | 生成 images/ |
| poster | poster.py | 对接平台发布 |

## 使用方式

### 单独运行

```bash
cd skills/asset-generator/scripts
python3 generate.py --game-id 169159534058 --date 2026-05-25
```

### 跳过图片生成（调试）

```bash
python3 generate.py --game-id 169159534058 --date 2026-05-25 --skip-images
```

### 跳过发布（只生成内容）

```bash
python3 generate.py --game-id 169159534058 --date 2026-05-25 --skip-post
```

### 自定义目录

```bash
python3 generate.py --game-id 169159534058 --date 2026-05-25 --data-dir /path/to/data --output-dir /path/to/output
```

## 教练语气原则

- "这一步如果这样走会更好"（不说"这一步太差了"）
- 亮点多于批评
- 具体指出"为什么"和"下次怎么想"
- 始终点名棋手（不是"白方"，而是"Aaron Wang"）

## 幂等性

- 若 `output/{game_id}/review.md` 和 `data.json` 已存在，跳过生成
- 手动删除 `output/{game_id}/` 可重新生成

## 错误处理

- data 目录不存在：报错退出（chess-analysis 可能未运行）
- metadata.json 或 engine_eval.json 缺失：报错退出
- 单个模块失败：打印错误但继续执行其他模块

## 发布平台接入

目前 placeholder 状态，需要配置各平台的 baoyu-post-to-* skill：

- `baoyu-post-to-xiaohongshu` — 小红书
- `baoyu-post-to-x` — X/Twitter
- `baoyu-post-to-weibo` — 微博
- `baoyu-post-to-video` — 视频号（future）

配置好平台后，移除 `generate.py` 中的 `--skip-post` 或去掉 poster.py 中的 placeholder 逻辑。