"""回归测试:引擎评估必须统一为白方视角,丢分必须按走子方计算。

背景:历史 bug 中 cp_score 用 pov_score.relative(轮到走子方视角),
导致评估符号每步翻转——白方占优被存成负分,残局白方完胜被误判成步步昏招。
"""
import sys
from pathlib import Path

import chess
import chess.engine

sys.path.insert(0, str(Path(__file__).parent))
from analyze import cp_score, centipawn_loss, is_missed_mate, EVAL_CLAMP


def _pov(cp, turn):
    return chess.engine.PovScore(chess.engine.Cp(cp), turn)


def _pov_mate(mate, turn):
    return chess.engine.PovScore(chess.engine.Mate(mate), turn)


# ---- cp_score 必须返回白方视角(正=白优,负=黑优),与轮到谁走无关 ----

def test_cp_score_white_winning_black_to_move():
    # 黑方视角 -8(黑方落后 8 兵) → 白方视角 +8
    assert cp_score(_pov(-800, chess.BLACK)) == 8.0


def test_cp_score_white_winning_white_to_move():
    # 白方视角 +8,轮到白走
    assert cp_score(_pov(800, chess.WHITE)) == 8.0


def test_cp_score_black_winning_regardless_of_turn():
    # 无论轮到谁走,黑方多 5 兵都应为白方视角 -5
    assert cp_score(_pov(500, chess.BLACK)) == -5.0   # 黑方视角 +5
    assert cp_score(_pov(-500, chess.WHITE)) == -5.0  # 白方视角 -5


def test_cp_score_mate_is_white_perspective():
    assert cp_score(_pov_mate(3, chess.WHITE)) == 1000.0    # 白方将杀
    assert cp_score(_pov_mate(3, chess.BLACK)) == -1000.0   # 黑方将杀 → 白方视角 -1000


# ---- centipawn_loss:走子方因这步损失多少(正=变差) ----

def test_white_move_losing_advantage_is_a_loss():
    # 白方视角 +9.0 → +8.5,白方走子,损失 0.5
    assert centipawn_loss(9.0, 8.5, "white") == 0.5


def test_white_winning_move_is_not_a_loss():
    # 残局白方完胜,+9.0 → +9.1,白方走子,损失为负(非昏着)
    assert centipawn_loss(9.0, 9.1, "white") < 0


def test_black_move_loss_uses_white_perspective_rise():
    # 白方视角 +2.0 → +5.0,黑方走子(走差了),黑方损失 3.0
    assert centipawn_loss(2.0, 5.0, "black") == 3.0


def test_winning_endgame_not_flagged_as_blunders():
    # 模拟白方完胜残局的白方着法序列:白方视角始终高位、小幅波动
    # 正确逻辑下,这些着法的 loss 都不应触发昏着(>1.0)
    white_pov_timeline = [9.0, 9.2, 8.9, 9.1, 9.0, 9.3]
    for prev, cur in zip(white_pov_timeline, white_pov_timeline[1:]):
        assert centipawn_loss(prev, cur, "white") <= 1.0


# ---- mate 哨兵值不得制造"错失速杀=丢上百兵"的误导性昏着 ----
# 背景:cp_score 用 ±1000 表示将杀。若直接拿去做减法,
# "原本将杀(+1000)→走完仍 +7.9 完胜"会被算成丢 992 兵的假昏着,
# 误导内容标题。正确处理:对决定性优势做钳制 + 单独标记"错失速杀"。

def test_missed_mate_while_winning_is_small_loss():
    # 白方原本将杀(+1000),走完仍 +7.9 完胜 → 实际葬送的优势很小,绝非 992
    loss = centipawn_loss(1000.0, 7.9, "white")
    assert 0 <= loss < 3.0


def test_black_missed_mate_while_winning_is_small_loss():
    loss = centipawn_loss(-1000.0, -7.9, "black")
    assert 0 <= loss < 3.0


def test_real_blunder_unaffected_by_clamp():
    # +7.72 → +0.44,白方葬送了真实大优势,钳制不应影响这种正常区间的丢分
    assert abs(centipawn_loss(7.72, 0.44, "white") - 7.28) < 0.01


def test_clamp_caps_runaway_loss():
    # 把将杀走成均势:钳制到 EVAL_CLAMP,而不是 1000
    assert centipawn_loss(1000.0, 0.0, "white") == EVAL_CLAMP
    assert EVAL_CLAMP >= 5.0


# ---- is_missed_mate:区分"错失速杀(仍完胜)" vs "真葬送优势" ----

def test_missed_mate_flagged_when_still_winning():
    assert is_missed_mate(1000.0, 7.9, "white") is True
    assert is_missed_mate(-1000.0, -7.9, "black") is True


def test_throwing_mate_into_equality_is_not_missed_mate():
    # 把将杀走成均势/劣势,不算"错失速杀",而是真昏着
    assert is_missed_mate(1000.0, 0.0, "white") is False
    assert is_missed_mate(1000.0, -8.0, "white") is False


def test_non_mate_position_never_missed_mate():
    assert is_missed_mate(7.72, 0.44, "white") is False
