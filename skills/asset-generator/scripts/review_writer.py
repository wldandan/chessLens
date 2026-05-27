"""生成教练式复盘文章"""
import json
from pathlib import Path

def generate_review(game_data: dict, engine_eval: dict) -> str:
    """
    生成教练式复盘文章。

    Args:
        game_data: metadata.json 内容
        engine_eval: engine_eval.json 内容

    Returns:
        review.md 内容字符串
    """
    white = game_data.get("white", "?")
    black = game_data.get("black", "?")
    result = game_data.get("result", "?")
    date = game_data.get("date", "?")
    opening = game_data.get("opening", "未知开局")
    time_control = game_data.get("time_control", "?")
    white_rating = game_data.get("white_rating", "?")
    black_rating = game_data.get("black_rating", "?")

    blunders = engine_eval.get("blunders", [])
    mistakes = engine_eval.get("mistakes", [])
    evaluations = engine_eval.get("evaluations", [])

    # 解析结果
    result_text = _parse_result(result, white)

    # 生成亮点时刻（从妙着生成）
    highlights = _extract_highlights(evaluations, white)

    lines = []

    # 标题
    lines.append(f"# {white} vs {black} | {date} | {result_text}\n")

    # 总体评价
    lines.append("## 总体评价")
    if len(blunders) == 0 and len(mistakes) == 0:
        overall = f"{white} 在{opening}中发挥稳健，没有明显失误。"
    elif len(blunders) == 0:
        overall = f"{white} 在{opening}中有一些小失误，但整体表现值得肯定。"
    elif len(blunders) <= 2:
        overall = f"{white} 在{opening}中既有亮点也有失误，是一盘有收获的对局。"
    else:
        overall = f"{white} 在{opening}中失误较多，但坚持到最后最终{result_text.split('（')[0].strip()}。"
    lines.append(overall)
    lines.append("")

    # 棋局概览
    lines.append("## 📊 棋局概览")
    lines.append(f"- **下棋时间**：{date}")
    lines.append(f"- **执白**：{white}（{white_rating}）")
    lines.append(f"- **执黑**：{black}（{black_rating}）")
    lines.append(f"- 比赛结果：**{result_text}**")
    lines.append(f"- 开局：{opening}")
    lines.append(f"- 时间控制：{time_control}秒")
    lines.append("")

    # 亮点时刻
    lines.append("## 🎯 亮点时刻")
    if highlights:
        for h in highlights[:3]:
            move_no = h.get("move_no", "?")
            san = h.get("san", "?")
            desc = h.get("description", "?")
            lines.append(f"- **第{move_no}步** — {san}：{desc}")
    else:
        lines.append("- 本局暂未发现明显亮点，继续加油！")
    lines.append("")

    # 关键失误
    lines.append("## ⚠️ 关键失误（按重要性排序）")
    all_errors = sorted(blunders + mistakes, key=lambda x: x.get("eval_drop", 0), reverse=True)
    if all_errors:
        for i, err in enumerate(all_errors[:3], 1):
            label = "💥" if err in blunders else "⚠️"
            move_no = err.get("move_no", "?")
            san = err.get("san", "?")
            eval_drop = err.get("eval_drop", 0)
            best_move = err.get("best_move", "?")
            lines.append(f"{i}. **第{move_no}步** — {label}")
            lines.append(f"   - 跌 **{eval_drop:.2f} 兵**")
            lines.append(f"   - 推荐着法：`{best_move}`")
            reason = f"   - 原因：第{move_no}步走了 {san}，"
            if eval_drop > 1.0:
                reason += "这是一步较大的失误，"
            reason += f"如果走 {best_move} 会更好。"
            lines.append(reason)
    else:
        lines.append("本局没有明显失误，继续保持！")
    lines.append("")

    # 可以更好的地方
    lines.append("## 💡 可以更好的地方")
    if highlights:
        lines.append(f"- {highlights[0].get('description', '继续深化对开局原理的理解')}")
    if mistakes:
        lines.append("- 注意在中局保持局面评估的稳定性")
    lines.append("- 残局阶段注意子力协调和王的活跃性")
    lines.append("")

    # 开局学习建议
    lines.append("## 📚 开局学习建议")
    lines.append(f"- 本局使用{opening}，建议深入学习该开局的典型变化")
    lines.append("- 注意出子节奏，避免过早失去主动权")
    lines.append("")

    # 今日收获
    lines.append("## 🌟 今日收获")
    if all_errors:
        lines.append(f"- 认识到第{all_errors[0]['move_no']}步的着法可以改进")
    if "1-0" in result:
        lines.append("- 赢下这盘棋，复盘是进步的关键")
    elif "0-1" in result:
        lines.append("- 输掉这盘棋，复盘是进步的关键")
    else:
        lines.append("- 弈和这盘棋，复盘是进步的关键")
    lines.append("- 下棋不复盘=没下过，坚持复盘才能提高")

    return "\n".join(lines)


def _parse_result(result: str, focus_player: str) -> str:
    """解析结果为易读文本"""
    if result == "1-0":
        return f"{focus_player} 胜（对手投降）"
    elif result == "0-1":
        return f"{focus_player} 负（对手获胜）"
    elif result == "1/2-1/2":
        return f"{focus_player} 和"
    else:
        return result


def _extract_highlights(evaluations: list, focus_player: str) -> list:
    """从评估中提取亮点时刻"""
    highlights = []
    for ev in evaluations:
        # 评估大于 2.0 且非失误视为亮点
        if abs(ev.get("eval", 0)) >= 2.0 and not ev.get("is_blunder") and not ev.get("is_mistake"):
            eval_val = ev.get("eval", 0)
            if eval_val > 0:
                description = f"获得 +{eval_val:.2f} 局面优势"
            else:
                description = f"对手获得 {abs(eval_val):.2f} 优势"
            highlights.append({
                "move_no": ev.get("move_no", "?"),
                "side": ev.get("side", "?"),
                "san": ev.get("san", "?"),
                "description": description
            })
    return highlights[:3]


def write_review(game_id: str, output_dir: Path):
    """读取 data/game_id/ JSON，生成 review.md"""
    game_data_dir = Path(f"data/{game_id}")

    if not game_data_dir.exists():
        raise ValueError(f"Data directory not found: {game_data_dir}")

    metadata_path = game_data_dir / "metadata.json"
    engine_eval_path = game_data_dir / "engine_eval.json"

    if not metadata_path.exists():
        raise ValueError(f"metadata.json not found in {game_data_dir}")
    if not engine_eval_path.exists():
        raise ValueError(f"engine_eval.json not found in {game_data_dir}")

    game_data = json.loads(metadata_path.read_text(encoding="utf-8"))
    engine_eval = json.loads(engine_eval_path.read_text(encoding="utf-8"))

    review_content = generate_review(game_data, engine_eval)

    output_path = output_dir / "review.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(review_content, encoding="utf-8")
    return output_path