# ChessLens - AI Chess Review

国际象棋对局回顾网站，基于 GitHub Pages 自动部署。

## 项目结构

```
chess-reviews-summary/
├── docs/                          # 对局 markdown 文件
│   └── {日期}_{game_id}_{白方}_{胜负}_{黑方}_{回合数}步}_{time_control}.md
├── .github/workflows/
│   ├── deploy.yml                 # GitHub Actions 部署配置
│   └── generate.py                # HTML 生成脚本
├── _site/                         # 生成的静态网站（自动部署）
└── README.md
```

## 文件命名格式

```
{日期}_{game_id}_{白方}_{胜负}_{黑方}_{回合数}步}_{time_control}.md
```

示例：
```
2026-04-14_167293652644_aaronwang2026_执白胜_Clement924810_19步_10+0.md
```

| 字段 | 说明 | 示例 |
|------|------|------|
| 日期 | 对局日期 | 2026-04-14 |
| game_id | 唯一标识 | 167293652644 |
| 白方 | 执白方用户名 | aaronwang2026 |
| 胜负 | 执白方结果 | 执白胜 / 执白败 / 执黑胜 / 执黑和 |
| 黑方 | 执黑方用户名 | Clement924810 |
| 回合数 | 总回合数 | 19步 |
| time_control | 时间控制 | 10+0 / 30+0 |

## Markdown 文件格式

对局文件需包含以下标记用于统计：

```markdown
🎯 **亮点时刻**
- **第7步 Bb5** — 牵制黑格

⚠️ **关键失误**
1. **第9步 Rxd1** — 严重昏着
```

- `🎯` 下的 `- **` 列表项统计为亮点数
- `⚠️` 下的数字列表项统计为失误数

## 本地开发

```bash
# 安装依赖
pip install mistune

# 生成静态网站
python3 .github/workflows/generate.py

# 查看生成的 site
open _site/index.html
```

## 自动部署

推送到 `main` 分支后，GitHub Actions 自动：
1. 运行 `generate.py` 生成 HTML
2. 部署到 GitHub Pages

网站地址：`https://wldandan.github.io/chess-reviews-summary/`
# trigger build Tue May 12 18:45:56 CST 2026
