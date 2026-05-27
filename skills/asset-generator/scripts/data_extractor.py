"""从 JSON 数据提取结构化 data.json（供 infographic 用）"""
import json
from pathlib import Path

def extract_data(game_id: str) -> dict:
    """
    从 data/{game_id}/ 读取 JSON，输出 data.json 格式

    Args:
        game_id: 格式为 {date}_{game_id}，如 "2026-05-25_169159534058"

    Returns:
        dict: 结构化数据
    """
    # 从 game_id 解析出 date 和 actual_game_id
    # 格式: {date}_{game_id}
    parts = game_id.split("_", 1)
    if len(parts) == 2:
        date, actual_game_id = parts
    else:
        date = ""
        actual_game_id = game_id

    data_dir = Path(f"data/{game_id}")

    metadata = {}
    engine_eval = {"blunders": [], "mistakes": [], "evaluations": []}

    metadata_path = data_dir / "metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    engine_eval_path = data_dir / "engine_eval.json"
    if engine_eval_path.exists():
        engine_eval = json.loads(engine_eval_path.read_text(encoding="utf-8"))

    # 提取亮点
    highlights = _extract_highlights(engine_eval)

    # 提取失误
    blunders = engine_eval.get("blunders", [])
    mistakes = engine_eval.get("mistakes", [])

    return {
        "game_id": actual_game_id,
        "date": date,
        "summary": f"{metadata.get('white', '?')} vs {metadata.get('black', '?')}",
        "result": metadata.get("result", "?"),
        "opening": metadata.get("opening", "未知开局"),
        "white": metadata.get("white", "?"),
        "black": metadata.get("black", "?"),
        "highlights": highlights,
        "blunders": blunders[:5],  # 最多5个昏着
        "mistakes": mistakes[:5],  # 最多5个失误
        "rating_change": metadata.get("rating_change", {}),
        "evaluations": engine_eval.get("evaluations", [])
    }


def _extract_highlights(engine_eval: dict) -> list:
    """从妙着（非失误但评估高）提取 highlights"""
    evaluations = engine_eval.get("evaluations", [])
    highlights = []
    for ev in evaluations:
        eval_val = abs(ev.get("eval", 0))
        if eval_val >= 2.0 and not ev.get("is_blunder") and not ev.get("is_mistake"):
            highlights.append({
                "move_no": ev.get("move_no", "?"),
                "side": ev.get("side", "?"),
                "san": ev.get("san", "?"),
                "eval": ev.get("eval", 0),
                "description": f"获得 +{eval_val:.2f} 局面优势"
            })
    return highlights[:3]


def write_data_json(game_id: str, output_dir: Path):
    """读取数据并写入 output/{game_id}/data.json"""
    data = extract_data(game_id)
    output_path = output_dir / "data.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return output_path


# 简单测试
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        game_id = sys.argv[1]
        data = extract_data(game_id)
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print("Usage: python data_extractor.py <game_id>")