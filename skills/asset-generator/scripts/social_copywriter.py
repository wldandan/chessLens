"""生成社媒文案草稿 highlights.md"""
import json
from pathlib import Path

# 默认分析目标（可配置）
DEFAULT_FOCUS_USER = "aaronwang2026"


def generate_social_copy(game_data: dict, engine_eval: dict, focus_user: str = DEFAULT_FOCUS_USER) -> str:
    """
    生成社媒文案草稿 highlights.md

    从社媒传播角度设计：戏剧性、悬念感、人情味

    Args:
        game_data: metadata.json 内容
        engine_eval: engine_eval.json 内容
        focus_user: 分析目标棋手用户名

    Returns:
        highlights.md 字符串（可直接发布）
    """
    white = game_data.get("white", "?")
    black = game_data.get("black", "?")
    result = game_data.get("result", "?")
    date = game_data.get("date", "?")
    opening_full = game_data.get("opening", "未知开局")
    # 简化开局名
    opening = _simplify_opening(opening_full)

    evaluations = engine_eval.get("evaluations", [])
    blunders = engine_eval.get("blunders", [])
    mistakes = engine_eval.get("mistakes", [])

    # 判断分析目标棋手执白还是执黑
    is_white = focus_user.lower() == white.lower()
    focus_side = "white" if is_white else "black"
    opponent = black if is_white else white
    my_color = "执白" if is_white else "执黑"

    # 解析结果
    if "1-0" in result:
        if is_white:
            outcome = "险胜"
            outcome_desc = "白方获胜"
        else:
            outcome = "对手获胜"
            outcome_desc = "黑方获胜"
    elif "0-1" in result:
        if is_white:
            outcome = "告负"
            outcome_desc = "白方告负"
        else:
            outcome = "对手告负"
            outcome_desc = "黑方获胜"
    else:
        outcome = "弈和"
        outcome_desc = "握手言和"

    # 提取本方亮点（只看 focus_user 的妙着）
    my_highlights = _extract_my_highlights(evaluations, focus_side)

    # 取最重要的 2 个失误（只取 focus_user 的）
    my_errors = sorted(
        [e for e in blunders + mistakes if e.get("side") == focus_side],
        key=lambda x: x.get("eval_drop", 0),
        reverse=True
    )[:2]

    # 检查是否有绝杀机会被错过
    has_missed_checkmate = any("#" in e.get("best_move", "") or "MATE" in str(e.get("best_score", ""))
                               for e in my_errors)

    # === 开始生成文案 ===
    lines = []

    # 标题（戏剧性）
    lines.append(f"⚪ {white} vs {black} ⚫ | {date}")
    lines.append(f"**{opening}** {my_color} {outcome}")
    lines.append("")

    # 剧情概述（制造悬念）
    lines.append("## 📖 这盘棋的剧情")
    if my_highlights:
        best = my_highlights[0]
        lines.append(f"• 第{best['move_no']}步 **{best['san']}** {best['description']} ☀️")
    if my_errors:
        worst = my_errors[0]
        lines.append(f"• 第{worst['move_no']}步走出 **{worst['san']}**，错失良机")
    if has_missed_checkmate:
        lines.append("• 绝杀机会来临时，一定要看清楚！")
    lines.append("")

    # 亮点时刻（展示妙手）
    if my_highlights:
        lines.append("## 🎯 本局妙手")
        for h in my_highlights[:2]:
            side_label = "白" if h['side'] == 'white' else "黑"
            lines.append(f"• 第{h['move_no']}步 **{h['san']}**：{h['description']}")
        lines.append("")

    # 失误回顾（戏剧化但不打击）
    if my_errors:
        lines.append("## 💡 本局可以更好的地方")
        for err in my_errors[:2]:
            drop = err.get("eval_drop", 0)
            # 戏剧化描述失误
            if drop > 10:
                drama = "跌入深渊"
            elif drop > 5:
                drama = "局面崩盘"
            elif drop > 2:
                drama = "优势瓦解"
            else:
                drama = "略显被动"
            lines.append(f"• 第{err['move_no']}步 **{err['san']}** → 应走 **{err.get('best_move', '?')}**（{drama}）")
        lines.append("")

    # 一句话总结（hook）
    lines.append("## 💬 总结")
    summary = _generate_summary(is_white, result, my_highlights, my_errors, has_missed_checkmate)
    lines.append(summary)

    lines.append("")
    lines.append("#Chess #国际象棋 #棋局复盘 #aaronwang2026")

    return "\n".join(lines)


def _simplify_opening(opening_full: str) -> str:
    """从完整开局名提取核心部分"""
    if not opening_full:
        return "国际象棋"
    # 移除 "Game ... Variation" 等冗余部分
    parts = opening_full.split("Game")
    if len(parts) > 1:
        return parts[0].strip()
    # 提取第一个单词（通常是开局名）
    main = opening_full.split(",")[0].strip()
    if len(main) > 30:
        main = main[:27] + "..."
    return main


def _extract_my_highlights(evaluations: list, focus_side: str) -> list:
    """只提取 focus_side 的妙着（评估 >= 2.0 且非失误）"""
    highlights = []
    for ev in evaluations:
        if ev.get("side") != focus_side:
            continue
        eval_val = abs(ev.get("eval", 0))
        if eval_val >= 2.0 and not ev.get("is_blunder") and not ev.get("is_mistake"):
            highlights.append({
                "move_no": ev.get("move_no", "?"),
                "side": ev.get("side", "?"),
                "san": ev.get("san", "?"),
                "description": f"获得 +{eval_val:.2f} 局面优势"
            })
    return highlights[:3]


def _generate_summary(is_win: bool, result: str, highlights: list, errors: list, missed_checkmate: bool) -> str:
    """生成有 hook 的一句话总结"""
    # 有绝杀机会
    if missed_checkmate:
        return "绝杀机会来临时一定要看清楚——这可能是胜负的关键！"

    # 赢了
    if "1-0" in result:
        if highlights and errors:
            return f"妙手奠定胜局，但中后段还需更稳——赢下来了，继续加油！💪"
        elif highlights:
            return "一盘漂亮的胜利！妙手连连，继续保持！🏆"
        elif errors:
            return "虽有问题但坚持到最后，胜利属于不放弃的人！🔥"
        else:
            return "稳稳拿下！每一盘棋都是积累，继续保持！💪"

    # 输了
    elif "0-1" in result:
        if errors:
            worst = errors[0]
            return f"第{worst['move_no']}步的失误是关键，复盘收获满满，下次会更好！"
        return "输棋不输心态，每一次复盘都是进步的机会！💪"

    # 和棋
    else:
        return "势均力敌的一局，继续打磨，下次争取拿下！🤝"


def write_highlights(game_id: str, output_dir: Path):
    """读取数据生成 highlights.md"""
    data_dir = Path(f"data/{game_id}")

    if not data_dir.exists():
        raise ValueError(f"Data directory not found: {data_dir}")

    game_data = json.loads((data_dir / "metadata.json").read_text(encoding="utf-8"))
    engine_eval = json.loads((data_dir / "engine_eval.json").read_text(encoding="utf-8"))

    content = generate_social_copy(game_data, engine_eval)
    output_path = output_dir / "highlights.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        game_id = sys.argv[1]
        # Test by printing to stdout
        print(f"Highlights written. Run with write_highlights() to save.")
    else:
        print("Usage: python social_copywriter.py <game_id>")