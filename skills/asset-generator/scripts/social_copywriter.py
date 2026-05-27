"""生成社媒文案草稿 highlights.md"""
import json
from pathlib import Path

def generate_social_copy(game_data: dict, engine_eval: dict) -> str:
    """
    生成社媒文案草稿 highlights.md

    Args:
        game_data: metadata.json 内容
        engine_eval: engine_eval.json 内容

    Returns:
        highlights.md 字符串（可直接发布）
    """
    white = game_data.get("white", "?")
    black = game_data.get("black", "?")
    result = game_data.get("result", "?")
    date = game_data.get("date", "?")
    opening = game_data.get("opening", "未知开局")

    evaluations = engine_eval.get("evaluations", [])
    blunders = engine_eval.get("blunders", [])
    mistakes = engine_eval.get("mistakes", [])

    # 提取亮点
    highlights = _extract_highlights(evaluations)

    # 取最重要的 3 个失误
    all_errors = sorted(blunders + mistakes, key=lambda x: x.get("eval_drop", 0), reverse=True)[:3]

    # 解析结果
    result_emoji = "✅" if "1-0" in result else "❌" if "0-1" in result else "🤝"

    lines = []
    lines.append(f"# {white} vs {black} | {date} {result_emoji}\n")
    lines.append(f"**{opening}** | {'执白' if white == 'aaronwang2026' else '执黑'}\n")

    # Hook line
    lines.append("## 🎯 这盘棋的亮点")
    if highlights:
        for h in highlights[:2]:
            lines.append(f"- **{'第'+str(h['move_no'])+'步'}** {h['san']}：{h['description']}")
    else:
        lines.append("- 坚持到最后，信念坚定！")
    lines.append("")

    # Mistakes
    lines.append("## 💡 可以更好的地方")
    if all_errors:
        for err in all_errors[:2]:
            lines.append(f"- 第{err['move_no']}步 {err.get('san', '?')}：应走 {err.get('best_move', '?')}（跌 {err.get('eval_drop', 0):.1f} 兵）")
    else:
        lines.append("- 没有明显失误，继续保持！")
    lines.append("")

    # 一句话总结
    lines.append("## 📝 一句话总结")
    if "1-0" in result:
        summary = "赢下这盘棋！"
    elif "0-1" in result:
        summary = "输掉这盘棋，但学到很多。"
    else:
        summary = "弈成一盘和棋，继续努力。"
    lines.append(f"{white} {summary}")
    lines.append("")

    # Tags
    lines.append("#Chess #国际象棋 #棋局复盘 #aaronwang2026")

    return "\n".join(lines)


def _extract_highlights(evaluations: list) -> list:
    """从妙着提取亮点"""
    highlights = []
    for ev in evaluations:
        eval_val = abs(ev.get("eval", 0))
        if eval_val >= 2.0 and not ev.get("is_blunder") and not ev.get("is_mistake"):
            highlights.append({
                "move_no": ev.get("move_no", "?"),
                "san": ev.get("san", "?"),
                "description": f"获得 +{eval_val:.2f} 优势"
            })
    return highlights[:2]


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