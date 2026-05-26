---
name: chess-player-stats
description: >
  获取国际象棋玩家的统计数据。当用户说"查一下某人水平"、
  "获取玩家信息"、"某人的 rating"、"玩家 stats"、
  "league"、"段位"、"积分"时触发此 skill。
  同时当用户发送 chess.com 用户名并要求查看其数据时触发。
---

# Chess Player Stats Skill

获取 chess.com 玩家的完整统计数据。

**默认用户**：若未指定用户名，则读取环境变量 `$CURRENT_CHESS_USER`。

## Input

- **username** (required): chess.com 用户名（若请求时未指定，自动使用 `$CURRENT_CHESS_USER`；若环境变量也未设置，则默认 `aaronwang2026`）

## Data Sources

### API Endpoints

```bash
# 玩家基本信息
curl "https://api.chess.com/pub/player/{username}"

# 玩家统计数据
curl "https://api.chess.com/pub/player/{username}/stats"
```

## Output Format

返回以下结构化数据：

```json
{
  "username": "magnuscarlsen",
  "title": "GM",
  "league": "Champion",
  "followers": 290355,
  "joined": 1282856720,
  "ratings": {
    "chess_rapid": {
      "last": 2941,
      "best": 2977
    },
    "chess_blitz": {
      "last": 3373,
      "best": 3401
    },
    "chess_bullet": {
      "last": 3257,
      "best": 3390
    }
  },
  "records": {
    "chess_rapid": {"win": 107, "loss": 26, "draw": 95},
    "chess_blitz": {"win": 4653, "loss": 1039, "draw": 802},
    "chess_bullet": {"win": 1427, "loss": 470, "draw": 217}
  }
}
```

**API 获取方式：**
```bash
curl "https://api.chess.com/pub/player/{username}/stats"
```
stats 接口同时返回 `ratings` 和 `record`（胜/负/平），一次请求获取全部数据，无需额外请求。

## Response Style

展示玩家数据时，使用以下格式：

```
⚔️ {username} 的数据统计

🏅 段位: {league}
📛 称号: {title || "无"}
👥 粉丝: {followers}

📊 等级分:
   ⚡ 闪电战(Blitz): {chess_blitz.last} (最高: {chess_blitz.best})
   ⏰ 快棋(Rapid): {chess_rapid.last} (最高: {chess_rapid.best})
   💨 超快棋(Bullet): {chess_bullet.last} (最高: {chess_bullet.best})

📈 战绩:
   闪电战: 胜 {win} / 负 {loss} / 平 {draw} ({total} 盘)
   快棋:   胜 {win} / 负 {loss} / 平 {draw} ({total} 盘)
   超快棋: 胜 {win} / 负 {loss} / 平 {draw} ({total} 盘)

🌍 全球排名:
   注: Chess.com 公开 API 不提供全球排名数据。
   如需全球排名，请访问: https://www.chess.com/ratings (手动查询)
   或通过 FIDE 官网 https://ratings.fide.com/ 查询真实国际等级分排名。
```

## Important Notes

- chess.com API 是公开的，**无需 API key**
- 请求频率限制：约 1 req/sec，避免短时间内大量请求
- 如果用户不存在，API 返回 404，告知用户
- league 可能的值：Champion, Gold, Silver, Bronze, 或 null

## Error Handling

- 用户不存在：`{error: "User not found: {username}"}`
- API 请求失败：`{error: "Failed to fetch stats: {reason}"}`
- 请求过快：`{error: "Rate limited, please wait"}`
