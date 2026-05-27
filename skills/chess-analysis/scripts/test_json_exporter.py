import json
from pathlib import Path
import tempfile
import sys
sys.path.insert(0, str(Path(__file__).parent))
from json_exporter import export_game_data, export_engine_eval, export_metadata

def test_export_metadata():
    metadata = {
        "game_id": "169159534058",
        "white": "aaronwang2026",
        "white_rating": 1457,
        "black": "itsbishara",
        "black_rating": 1425,
        "result": "1-0",
        "date": "2026-05-25",
        "time_control": "600",
        "opening": "Giuoco Piano",
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "metadata.json"
        export_metadata(metadata, output_path)
        assert output_path.exists()
        data = json.load(open(output_path))
        assert data["game_id"] == "169159534058"

def test_export_engine_eval():
    evaluations = [
        {"move_no": 1, "side": "white", "eval": -0.45, "is_blunder": False, "is_mistake": False}
    ]
    blunders = [
        {"move_no": 14, "side": "white", "san": "Nh4", "eval_drop": 3.12, "best_move": "Nf3", "best_eval": 2.65}
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "engine_eval.json"
        export_engine_eval("169159534058", 16, evaluations, blunders, [], output_path)
        assert output_path.exists()
        data = json.load(open(output_path))
        assert data["game_id"] == "169159534058"
        assert len(data["blunders"]) == 1