"""JSON exporter for chess analysis data."""
import json
from pathlib import Path

def export_game_data(game_id: str, pgn_data: dict, output_dir: Path):
    """Export game data to pgn.json."""
    output_path = output_dir / "pgn.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"game_id": game_id, **pgn_data}, f, ensure_ascii=False, indent=2)

def export_engine_eval(game_id: str, depth: int, evaluations: list,
                       blunders: list, mistakes: list, output_path: Path):
    """Export engine evaluation to engine_eval.json."""
    data = {
        "game_id": game_id,
        "depth": depth,
        "evaluations": evaluations,
        "blunders": blunders,
        "mistakes": mistakes
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def export_metadata(metadata: dict, output_path: Path):
    """Export game metadata to metadata.json."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)