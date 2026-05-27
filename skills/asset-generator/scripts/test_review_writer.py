import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from review_writer import generate_review

def test_generate_review_basic():
    game_data = {
        "game_id": "169159534058",
        "white": "aaronwang2026",
        "black": "itsbishara",
        "result": "1-0",
        "date": "2026-05-25",
        "opening": "Giuoco Piano",
        "time_control": "600",
        "white_rating": 1457,
        "black_rating": 1425
    }
    engine_eval = {
        "evaluations": [
            {"move_no": 1, "side": "white", "eval": -0.45, "is_blunder": False, "is_mistake": False},
            {"move_no": 13, "side": "white", "eval": 2.65, "is_blunder": False, "is_mistake": False, "san": "Qxd4"},
        ],
        "blunders": [
            {"move_no": 36, "side": "white", "san": "Rb5+", "eval_drop": 1007.90, "best_move": "Ra8#", "best_score": "MATE"}
        ],
        "mistakes": [
            {"move_no": 35, "side": "white", "san": "Ba6", "eval_drop": 19.80, "best_move": "Re7", "best_score": "-10.65"}
        ]
    }
    result = generate_review(game_data, engine_eval)
    assert "aaronwang2026" in result
    assert "Giuoco Piano" in result
    assert "1-0" in result or "胜" in result
    assert len(result) > 100
    # Should mention the blunder
    assert "Rb5" in result
    # Should use encouraging tone
    assert "如果" in result or "更好" in result or "下次" in result