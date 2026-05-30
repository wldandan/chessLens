#!/usr/bin/env python3
"""
生成纯棋盘图（无文字叠加），用于在ljg-card中组合使用
"""
import sys
import os
import json
import math
import argparse
import chess
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_board import draw_board, get_move_squares

ARROW_RED = (220, 50, 50)
ARROW_GREEN = (50, 200, 100)
SQUARE_SIZE = 60
COORD_MARGIN = 24
BOARD_PX = 480

def sq_center(sq, sq_size=SQUARE_SIZE, coord_margin=COORD_MARGIN, flipped=False):
    f = chess.square_file(sq)
    r = chess.square_rank(sq)
    if flipped:
        col, row = 7 - f, r
    else:
        col, row = f, 7 - r
    cx = col * sq_size + coord_margin + sq_size // 2
    cy = row * sq_size + coord_margin + sq_size // 2
    return cx, cy

def draw_thin_arrow(draw, fx, fy, tx, ty, color, alpha=160):
    dx, dy = tx - fx, ty - fy
    length = math.hypot(dx, dy)
    if length == 0:
        return

    ux, uy = dx / length, dy / length
    px, py = -uy, ux

    shaft_w = 4
    head_w = 10
    head_len = 16

    shaft_end_x = tx - ux * head_len
    shaft_end_y = ty - uy * head_len

    shaft = [
        (fx + px * shaft_w, fy + py * shaft_w),
        (fx - px * shaft_w, fy - py * shaft_w),
        (shaft_end_x - px * shaft_w, shaft_end_y - py * shaft_w),
        (shaft_end_x + px * shaft_w, shaft_end_y + py * shaft_w),
    ]
    head = [
        (shaft_end_x + px * head_w, shaft_end_y + py * head_w),
        (shaft_end_x - px * head_w, shaft_end_y - py * head_w),
        (tx, ty),
    ]

    rgba = color + (alpha,)
    draw.polygon(shaft, fill=rgba)
    draw.polygon(head, fill=rgba)


def add_coords(img, flipped=False):
    """添加a-h和1-8坐标"""
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('/Library/Fonts/Arial Unicode.ttf', 18)
    except:
        font = ImageFont.load_default()

    TEXT_GRAY = (138, 138, 163)

    for f in range(8):
        col = f if not flipped else 7 - f
        x = col * SQUARE_SIZE + COORD_MARGIN + SQUARE_SIZE // 2
        y = BOARD_PX + 8
        label = chr(ord('a') + f)
        bbox = draw.textbbox((0, 0), label, font=font)
        w = bbox[2] - bbox[0]
        draw.text((x - w // 2, y), label, font=font, fill=TEXT_GRAY)

    for r in range(8):
        row = 7 - r if not flipped else r
        x = 4
        y = row * SQUARE_SIZE + COORD_MARGIN + SQUARE_SIZE // 2
        label = str(r + 1)
        bbox = draw.textbbox((0, 0), label, font=font)
        draw.text((x, y - bbox[3] // 2), label, font=font, fill=TEXT_GRAY)


def _safe_move_squares(fen, san):
    """解析 SAN -> (from_sq, to_sq)，非法/缺失时返回 (None, None)。"""
    if not san or san == "?":
        return None, None
    try:
        return get_move_squares(fen, san)
    except Exception:
        return None, None


def generate_clean_board(game_id, step, side, fen, mistake_san, best_san, loss, output_dir):
    """生成纯棋盘图（无文字叠加）"""
    flipped = (side == '黑')

    img_mistake = draw_board(fen=fen, arrows=[], flipped=flipped, highlight_last=False)
    img_best = draw_board(fen=fen, arrows=[], flipped=flipped, highlight_last=False)

    add_coords(img_mistake, flipped)
    add_coords(img_best, flipped)

    mistake_from, mistake_to = _safe_move_squares(fen, mistake_san)
    best_from, best_to = _safe_move_squares(fen, best_san)

    draw_m = ImageDraw.Draw(img_mistake)
    if mistake_from:
        fx, fy = sq_center(mistake_from, flipped=flipped)
        tx, ty = sq_center(mistake_to, flipped=flipped)
        draw_thin_arrow(draw_m, fx, fy, tx, ty, ARROW_RED, alpha=180)

    draw_b = ImageDraw.Draw(img_best)
    if best_from:
        fx, fy = sq_center(best_from, flipped=flipped)
        tx, ty = sq_center(best_to, flipped=flipped)
        draw_thin_arrow(draw_b, fx, fy, tx, ty, ARROW_GREEN, alpha=180)

    # 上下合并
    board_h = img_mistake.height
    sep_h = 80
    total_h = board_h * 2 + sep_h
    board_w = img_mistake.width

    combined = Image.new('RGB', (board_w, total_h), (26, 26, 46))
    combined.paste(img_mistake, (0, 0))

    # 下半部分棋盘
    combined.paste(img_best, (0, board_h + sep_h))

    # 保存
    filename = f"{game_id}_blunder_{step}_clean.png"
    filepath = os.path.join(output_dir, filename)
    combined.save(filepath)
    print(f"保存: {filepath}  (第{step}步 {mistake_san} 丢{loss:.2f}, 应走 {best_san})")
    return filepath


def load_top_blunders(data_dir, top_n=3):
    """从 engine_eval.json + pgn.json 读取 TOP-N 真·昏着（按 eval_drop 倒序）。

    关键：只取 blunders，按丢分排序；missed_wins（错失速杀，仍完胜）单独，不混入。
    FEN 取「失误着法之前」的局面（= 上一手之后的 FEN），箭头才标得对。
    """
    with open(os.path.join(data_dir, "engine_eval.json"), encoding="utf-8") as f:
        ev = json.load(f)
    with open(os.path.join(data_dir, "pgn.json"), encoding="utf-8") as f:
        pgn = json.load(f)

    moves = pgn["moves"]
    game_id = ev.get("game_id") or pgn.get("game_id", "unknown")
    blunders = sorted(ev.get("blunders", []), key=lambda b: b["eval_drop"], reverse=True)[:top_n]

    examples = []
    for b in blunders:
        move_no, side = b["move_no"], b["side"]
        ply = (move_no - 1) * 2 + (0 if side == "white" else 1)
        fen_before = moves[ply - 1]["fen"] if ply > 0 else chess.STARTING_FEN
        side_cn = "白" if side == "white" else "黑"
        examples.append((game_id, move_no, side_cn, fen_before,
                         b["san"], b.get("best_move", "?"), b.get("eval_drop", 0.0)))
    return examples


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="从 engine_eval.json + pgn.json 生成 TOP-N 昏着棋盘图（数据驱动，不写死）")
    parser.add_argument("--data-dir", required=True,
                        help="含 engine_eval.json 与 pgn.json 的目录，如 data/2026-05-24_169159534058/")
    parser.add_argument("--output-dir", help="图片输出目录（默认 <data-dir>/images）")
    parser.add_argument("--top", type=int, default=3, help="生成前 N 个昏着，默认 3")
    args = parser.parse_args()

    out_dir = args.output_dir or os.path.join(args.data_dir, "images")
    os.makedirs(out_dir, exist_ok=True)

    examples = load_top_blunders(args.data_dir, args.top)
    if not examples:
        print("未发现昏着（blunders 为空）。")
    for game_id, step, side, fen, mistake, best, loss in examples:
        generate_clean_board(game_id, step, side, fen, mistake, best, loss, out_dir)