#!/usr/bin/env python3
"""
为每个失误生成棋盘截图，带箭头标注失误着法和正确着法
"""
import sys
import os
import chess
from PIL import Image, ImageDraw, ImageFont

# 添加scripts目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_board import draw_board, get_move_squares

IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'images')

# 失误数据：(game_id, step, side, fen_before, mistake_san, best_san)
# FEN是失误着法之前的局面（不是之后！），这样箭头才能正确标注
# Step 37: Ra7+ is the correct move, Rb5+ was the mistake
# Step 36: Kf2 is correct, c7+ was mistake
# Step 35: Re7 is correct, Ba6 was mistake
MISTAKE_EXAMPLES = [
    ('169159534058', 37, '白', '2k5/1RP5/B3bp1p/2p3p1/2P5/5P2/PP4PP/6K1 w - - 1 37', 'Rb5+', 'Ra7+'),
    ('169159534058', 36, '白', '3k4/1R6/B1P1bp1p/2p3p1/2P5/5P2/PP4PP/6K1 w - - 5 36', 'c7+', 'Kf2'),
    ('169159534058', 35, '白', '2k5/1R6/2P1bp1p/1Bp3p1/2P5/5P2/PP4PP/6K1 w - - 3 35', 'Ba6', 'Re7'),
]

# 颜色
ARROW_RED = (220, 50, 50)
ARROW_GREEN = (50, 200, 100)

def generate_blunder_image(game_id, step, side, fen, mistake_san, best_san, num, total):
    """生成失误对比图：显示失误着法和正确着法"""
    # 判断是否翻转（黑方回合）
    flipped = (side == '黑')

    # 获取失误着法的箭头
    mistake_from, mistake_to = get_move_squares(fen, mistake_san)
    mistake_arrow = [(mistake_from, mistake_to, ARROW_RED)] if mistake_from else []

    # 获取正确着法的箭头
    best_from, best_to = get_move_squares(fen, best_san)
    best_arrow = [(best_from, best_to, ARROW_GREEN)] if best_from else []

    # 生成两个棋盘图
    img_mistake = draw_board(fen=fen, arrows=mistake_arrow, flipped=flipped)
    img_best = draw_board(fen=fen, arrows=best_arrow, flipped=flipped)

    # 合并成一张图 (并排)
    combined = Image.new('RGB', (img_mistake.width * 2 + 20, img_mistake.height), (26, 26, 46))
    combined.paste(img_mistake, (0, 0))
    combined.paste(img_best, (img_mistake.width + 20, 0))

    # 添加文字
    draw = ImageDraw.Draw(combined)

    # 添加标题 (英文避免Unicode问题)
    title = f"Move {step} Mistake ({num}/{total})"
    draw.text((10, 10), title, fill=(255, 255, 255))
    draw.text((10, img_mistake.height - 30), f"Mistake: {mistake_san}", fill=(255, 100, 100))
    draw.text((img_mistake.width + 30, img_mistake.height - 30), f"Correct: {best_san}", fill=(100, 255, 100))

    # 保存
    filename = f"{game_id}_blunder_{step}.png"
    filepath = os.path.join(IMAGES_DIR, filename)
    combined.save(filepath)
    print(f"保存: {filepath}")
    return filename

if __name__ == "__main__":
    for i, (game_id, step, side, fen, mistake, best) in enumerate(MISTAKE_EXAMPLES, 1):
        generate_blunder_image(game_id, step, side, fen, mistake, best, i, len(MISTAKE_EXAMPLES))
