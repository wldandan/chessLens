#!/usr/bin/env python3
"""
chess-analysis/scripts/analyze.py
批量分析 PGN：一次启动 Stockfish，逐局面评估，输出 Markdown 报告

用法：
  python3 analyze.py "PGN..." [depth]
  python3 analyze.py --pgn-file game.pgn [depth]
"""

import re
import sys
import chess
import chess.engine
import chess.pgn
import io
from pathlib import Path

DEFAULT_DEPTH = 16
DEFAULT_STOCKFISH_PATH = "/opt/homebrew/bin/stockfish"


def find_stockfish(stockfish_path=None):
    if stockfish_path and Path(stockfish_path).exists():
        return stockfish_path
    linux_paths = [
        "/usr/games/stockfish",
        "/usr/local/bin/stockfish",
        "/opt/homebrew/bin/stockfish",
        "/opt/homebrew/bin/stockfish-mac",
    ]
    for p in linux_paths:
        if Path(p).exists():
            return p
    return "stockfish"


def clean_pgn(pgn_text: str) -> str:
    """预处理 PGN，移除时钟注释等非标准内容。"""
    text = re.sub(r'\{[^{}]*\}', '', pgn_text)
    text = re.sub(r'\[%eval[^{}]*\]', '', text)
    text = re.sub(r'\[%[^\]]*\]', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        if line.startswith('[') or line.strip() == '':
            cleaned_lines.append(line.rstrip())
        else:
            cleaned_lines.append(re.sub(r'\s+', ' ', line).strip())
    return '\n'.join(cleaned_lines).strip()


def parse_pgn(pgn_text: str) -> chess.pgn.Game:
    cleaned = clean_pgn(pgn_text)
    game = chess.pgn.read_game(io.StringIO(cleaned))
    if game is None:
        raise ValueError("无法解析 PGN，请检查格式")
    return game


def get_opening_name(eco_url: str) -> str:
    if not eco_url:
        return "未知开局"
    return eco_url.split("/")[-1].replace("-", " ")


def fmt_score(pov_score: chess.engine.PovScore) -> str:
    rs = pov_score.relative
    if rs.is_mate():
        mate = rs.mate()
        return f"Mate {'+' if mate > 0 else ''}{mate}"
    cp = rs.score() / 100
    return f"{'+' if cp >= 0 else ''}{cp:.2f}"


def eval_icon(pov_score: chess.engine.PovScore) -> str:
    rs = pov_score.relative
    if rs.is_mate():
        return "👑"
    cp = rs.score() / 100
    if cp >= 2.0:
        return "🟢"
    elif cp >= 0.5:
        return "🟡"
    elif cp >= -0.5:
        return "⚖️"
    elif cp >= -2.0:
        return "🔴"
    else:
        return "💀"


def cp_score(pov_score: chess.engine.PovScore) -> float:
    rs = pov_score.relative
    if rs.is_mate():
        return 1000.0 if rs.mate() > 0 else -1000.0
    return rs.score() / 100.0


def get_engine_best_move(engine, board, depth):
    """返回 (best_move_san, score_after, pv_san_list, explanation)"""
    try:
        info = engine.analyse(board, chess.engine.Limit(depth=depth))
        best_move = info["pv"][0] if "pv" in info and info["pv"] else None
        score = info.get("score", None)
        if best_move:
            try:
                san = board.san(best_move)
                # 获取完整 PV 线路
                pv_moves = info.get("pv", [])
                pv_san_list = []
                tmp_board = board.copy()
                for mv in pv_moves:
                    try:
                        pv_san_list.append(tmp_board.san(mv))
                        tmp_board.push(mv)
                    except Exception:
                        break
                return san, best_move, score, pv_san_list
            except Exception:
                return best_move.uci(), best_move, score, []
    except Exception:
        pass
    return None, None, None, []


def analyze_game(pgn_text: str, depth: int = DEFAULT_DEPTH, stockfish_path: str = None, focus_user: str = None):
    engine_path = find_stockfish(stockfish_path)
    engine = chess.engine.SimpleEngine.popen_uci(engine_path)

    try:
        game = parse_pgn(pgn_text)
    except Exception as e:
        engine.quit()
        raise e

    headers = dict(game.headers)
    white = headers.get("White", "?")
    black = headers.get("Black", "?")
    result = headers.get("Result", "?")
    eco_url = headers.get("ECOUrl", "")
    opening = get_opening_name(eco_url)
    tc = headers.get("TimeControl", "?")

    nodes = list(game.mainline())
    total = len(nodes)

    # 确定目标棋手的颜色（必须在打印 header 之前）
    white_player = headers.get("White", "?")
    black_player = headers.get("Black", "?")
    if focus_user is None:
        focus_user = black_player
    if focus_user.lower() == white_player.lower():
        focus_side_is_white = True
        focus_side_name = "白"
    else:
        focus_side_is_white = False
        focus_side_name = "黑"

    print("=" * 58)
    print(f"  🏁 {white} (⚪) vs {black} (⚫)  —  {result}")
    print(f"  📁 {opening}")
    print(f"  ⏱️  {tc}  |  共 {total//2} 步")
    if focus_user:
        print(f"  🎯 分析目标：{focus_user}（{focus_side_name}方）")
    print("=" * 58)
    print(f"\n📈 局面评估走势（depth={depth}）：")
    print(f"{'步':>5} {'着法':>10}  {'评估':>12}  {'趋势'}")
    print("-" * 55)

    prev_score = None
    prev_board = None
    mistakes = []
    blunders = []

    # 两遍扫描：第一遍记录失误，第二遍用引擎求最佳着法
    # 第一遍：只评估，不求最佳着法（节省时间）
    for i, node in enumerate(nodes):
        board = node.board()
        move_no = (i // 2) + 1
        side = "白" if i % 2 == 0 else "黑"
        san = node.san()

        try:
            info = engine.analyse(board, chess.engine.Limit(depth=depth))
            pov_score = info["score"]
        except Exception:
            pov_score = chess.engine.PovScore(
                chess.engine.Score(chess.engine.Cp(0), None), board.turn
            )

        ev_str = fmt_score(pov_score)
        icon = eval_icon(pov_score)

        marker = ""
        is_focus_move = (side == focus_side_name)
        if prev_score is not None:
            drop = cp_score(prev_score) - cp_score(pov_score)
            if drop > 1.0:
                marker = "💥 BLUNDER"
                if is_focus_move:
                    blunders.append({
                        "move_no": move_no,
                        "side": side,
                        "san": san,
                        "drop": drop,
                        "board_before": prev_board,
                        "node_idx": i - 1,
                    })
            elif drop > 0.3:
                marker = "⚠️ MISTAKE"
                if is_focus_move:
                    mistakes.append({
                        "move_no": move_no,
                        "side": side,
                        "san": san,
                        "drop": drop,
                        "board_before": prev_board,
                        "node_idx": i - 1,
                    })

        print(f"{move_no:>4}.{side:<3} {san:>10}  {icon}{ev_str:>12}  {marker}")

        prev_score = pov_score
        prev_board = board

    engine.quit()

    # 第二遍：用 Stockfish 计算每个失误局面的最佳着法
    print("\n" + "=" * 55)
    print("🔍 正在用 Stockfish 计算推荐着法...")
    engine2 = chess.engine.SimpleEngine.popen_uci(engine_path)
    try:
        all_errors = sorted(blunders + mistakes, key=lambda x: x["drop"], reverse=True)
        for err in all_errors:
            board_before = err["board_before"]
            if board_before is None:
                err["best_move"] = "?"
                err["best_score"] = "?"
                err["pv_line"] = []
                continue
            best_san, best_move, best_score, pv_line = get_engine_best_move(engine2, board_before, depth)
            err["best_move"] = best_san or "?"
            err["best_score"] = fmt_score(best_score) if best_score else "?"
            err["pv_line"] = pv_line or []
    finally:
        engine2.quit()

    # 输出失误详情
    print("\n💥 昏着（评估下跌 > 1.0 兵）：")
    if blunders:
        for b in sorted(blunders, key=lambda x: x["drop"], reverse=True):
            print(f"\n   🚨 第 {b['move_no']} 步（{b['side']}）：{b['san']}")
            print(f"      评估下跌：▼ {b['drop']:.2f} 兵")
            print(f"      正确走法：{b['best_move']}（评估 {b['best_score']}）")
            if b['pv_line']:
                pv_str = " → ".join(b['pv_line'][:6])
                print(f"      推荐变化：{pv_str}")
            print(f"      失误分析：第 {b['move_no']} 步走了 {b['san']}，让对手轻易消除了威胁/简化了局面/夺走了主动权")
    else:
        print("   无")

    print(f"\n\n⚠️ 失误（评估下跌 0.3~1.0 兵）：")
    if mistakes:
        for m in sorted(mistakes, key=lambda x: x["drop"], reverse=True):
            print(f"\n   ⚡ 第 {m['move_no']} 步（{m['side']}）：{m['san']}")
            print(f"      评估下跌：▼ {m['drop']:.2f} 兵")
            print(f"      正确走法：{m['best_move']}（评估 {m['best_score']}）")
            if m['pv_line']:
                pv_str = " → ".join(m['pv_line'][:6])
                print(f"      推荐变化：{pv_str}")
            print(f"      失误分析：第 {m['move_no']} 步走了 {m['san']}，这里有更好的选择，可以...（更好的走法能带来更好的局面发展）")
    else:
        print("   无")

    print(f"\n🎯 开局：{opening}")
    print("\n💡 关键局面 FEN（失误前局面）：")

    key_indices = set()
    for b in blunders[:3]:
        key_indices.add(b["node_idx"])
    for m in mistakes[:3]:
        key_indices.add(m["node_idx"])
    if total > 0:
        key_indices.add(total - 1)

    for idx in sorted(key_indices):
        node = nodes[idx]
        mno = (idx // 2) + 1
        side = "白" if idx % 2 == 0 else "黑"
        fen = node.board().fen()
        print(f"  {mno}.{side}: {fen}")


if __name__ == "__main__":
    pgn_input = None
    depth = DEFAULT_DEPTH
    stockfish_path = None
    focus_user = None  # 目标棋手，默认分析黑方（由用户指定）

    args = sys.argv[1:]
    if not args:
        print("用法：python3 analyze.py \"PGN...\" [depth] [--stockfish-path PATH] [--focus-user USERNAME]", file=sys.stderr)
        print("      python3 analyze.py --pgn-file game.pgn [depth] [--stockfish-path PATH] [--focus-user USERNAME]", file=sys.stderr)
        print("      python3 analyze.py --focus-user aaronwang2026 --pgn-file game.pgn 18", file=sys.stderr)
        sys.exit(1)

    i = 0
    pgn_file_used = False
    while i < len(args):
        if args[i] == "--pgn-file":
            with open(args[i + 1]) as f:
                pgn_input = f.read()
            pgn_file_used = True
            i += 2
        elif args[i] == "--stockfish-path":
            stockfish_path = args[i + 1]
            i += 2
        elif args[i] == "--focus-user":
            focus_user = args[i + 1]
            i += 2
        else:
            if args[i].startswith("-"):
                try:
                    depth = int(args[i])
                except ValueError:
                    pass
            else:
                if not pgn_file_used and pgn_input is None:
                    pgn_input = args[i]
            i += 1

    if not pgn_input:
        print("错误：未提供 PGN 内容", file=sys.stderr)
        sys.exit(1)

    try:
        analyze_game(pgn_input, depth, stockfish_path, focus_user)
    except Exception as ex:
        print(f"错误：{ex}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
