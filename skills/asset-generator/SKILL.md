---
name: asset-generator
description: >
  将 chess-analysis 输出的 JSON 数据转换为内容发布包。
  输入 data/{date}_{game_id}/ 目录，输出 output/{date}_{game_id}/ 包含 review.md、data.json、highlights.md 和 images/。
  当用户说"生成发布内容"、"制作复盘素材"、"这盘棋做图文"时触发。
---

# asset-generator Skill

读取 `data/{game_id}/` 下的 JSON 文件，生成可发布的复盘内容。

## 输入

- **game_id** (required): 对局 ID，格式为 `data/YYYY-MM-DD_{game_id}/`

## 输出

```
output/{date}_{game_id}/
├── review.md         # 教练式复盘文章
├── data.json         # 结构化数据（供 infographic 用）
├── highlights.md     # 社媒文案草稿
└── images/
    ├── board.png         # 棋盘截图
    ├── infographic.png   # 信息图
    └── thumbnail.jpg     # 视频封面
```

## 子模块

- `review_writer.py` — 生成 review.md
- `data_extractor.py` — 生成 data.json
- `social_copywriter.py` — 生成 highlights.md
- `image_generator.py` — 生成 images/
- `poster.py` — 对接平台发布
- `generate.py` — 主入口，调度各子模块

## 使用方式

```bash
python3 scripts/generate.py --game-id 169159534058 --date 2026-05-25
```

## 教练语气原则

- "这一步如果这样走会更好"（不说"这一步太差了"）
- 亮点多于批评
- 具体指出"为什么"和"下次怎么想"
- 始终点名棋手（不是"白方"，而是"Aaron Wang"）

## 幂等性

- 若 output/{game_id}/ 已存在，跳过生成
- 各子模块可独立运行，调试方便