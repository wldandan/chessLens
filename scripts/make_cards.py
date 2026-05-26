#!/usr/bin/env python3
"""
Create 1920×1080 video cards for Aaron's Chess Journey.
Each card is a PIL Image ready to be assembled into a video.
"""

from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

# ── Canvas ──────────────────────────────────────────────────────────────────
W, H = 1920, 1080

# ── ChessLens palette ────────────────────────────────────────────────────────
BG       = ( 26,  26,  46)   # #1a1a2e  – deep navy
CARD     = ( 22,  33,  62)   # #16213e  – card surface
GOLD     = (230, 184,   0)   # #e6b800  – brand gold
GREEN    = ( 74, 222, 128)   # #4ade80  – good move
RED      = (248, 113, 113)   # #f87171  – mistake
AMBER    = (245, 158,  11)   # #f59e0b  – warning / draw
TEXT     = (241, 245, 249)   # #f1f5f9  – primary text
MUTED    = (148, 163, 184)   # #94a3b8  – secondary text
BORDER   = ( 51,  65,  85)   # #334155  – divider

# Board render size and its position in the left panel
BOARD_SZ   = 640
LEFT_W     = 900
BOARD_X    = (LEFT_W - BOARD_SZ) // 2          # 130
BOARD_Y    = (H       - BOARD_SZ) // 2          # 220
RIGHT_X    = LEFT_W + 60                        # 960
RIGHT_W    = W - RIGHT_X - 60                   # 900

# ── Fonts ────────────────────────────────────────────────────────────────────
_FONT_PATHS = [
    '/Library/Fonts/Arial Unicode.ttf',        # chess symbols + CJK
    '/System/Library/Fonts/STHeiti Medium.ttc',
    '/System/Library/Fonts/Helvetica.ttc',
]

def _find_font():
    for p in _FONT_PATHS:
        if os.path.exists(p):
            return p
    return None

_FONT_PATH = _find_font()


def font(size):
    if _FONT_PATH:
        try:
            return ImageFont.truetype(_FONT_PATH, size)
        except Exception:
            pass
    return ImageFont.load_default()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _blank():
    img = Image.new('RGB', (W, H), BG)
    return img, ImageDraw.Draw(img)


def _wrap(text, max_chars=28):
    """Simple character-count word-wrap for mixed CJK/ASCII text."""
    lines = []
    for para in text.split('\n'):
        if len(para) <= max_chars:
            lines.append(para)
        else:
            # Try textwrap first (good for pure ASCII)
            wrapped = textwrap.wrap(para, width=max_chars)
            if wrapped:
                lines.extend(wrapped)
            else:
                # Brute-force split for CJK
                while len(para) > max_chars:
                    lines.append(para[:max_chars])
                    para = para[max_chars:]
                if para:
                    lines.append(para)
    return lines


def _text_block(draw, lines, x, y, fnt, color=TEXT, line_h=None):
    """Draw multiple lines; return y position after last line."""
    lh = line_h or (fnt.size + 10)
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=color)
        y += lh
    return y


def _badge(draw, x, y, label, bg_color, text_color=BG, pad_x=28, pad_h=16, fnt=None):
    """Draw a pill-shaped badge. Returns (right_x, center_y)."""
    fnt = fnt or font(32)
    bbox = fnt.getbbox(label)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    bw = tw + pad_x * 2
    bh = th + pad_h * 2
    draw.rounded_rectangle([x, y, x + bw, y + bh], radius=bh // 2, fill=bg_color)
    draw.text((x + pad_x, y + pad_h), label, font=fnt, fill=text_color)
    return x + bw, y + bh // 2


def _result_badge(draw, result, x, y, fnt=None):
    fnt = fnt or font(36)
    mapping = {
        'win':  ('  胜  ', GREEN),
        'loss': ('  负  ', RED),
        'draw': ('  和  ', AMBER),
    }
    label, color = mapping.get(result, ('  ?  ', MUTED))
    _badge(draw, x, y, label, color, fnt=fnt)


def _divider(draw, y, x0=RIGHT_X, x1=W - 60, color=BORDER):
    draw.line([(x0, y), (x1, y)], fill=color, width=1)


def _place_board(img, board_img):
    """Paste a board image into the left panel."""
    board_rgb = board_img.convert('RGB') if board_img.mode != 'RGB' else board_img
    scaled = board_rgb.resize((BOARD_SZ, BOARD_SZ), Image.LANCZOS)
    img.paste(scaled, (BOARD_X, BOARD_Y))


def _left_panel_bg(draw):
    """Subtle card background for the left board panel."""
    draw.rectangle([0, 0, LEFT_W - 1, H], fill=CARD)


def _logo_text(draw, y=36):
    """Small ChessLens logo in top-left."""
    draw.text((36, y), '♟ ChessLens', font=font(24), fill=GOLD)


def _series_label(draw, game_number, y=36):
    """'Aaron's Chess Journey · Game #N' in top-right area."""
    label = f"Aaron's Chess Journey  ·  Game #{game_number}"
    draw.text((RIGHT_X, y), label, font=font(24), fill=MUTED)


# ── Card factories ────────────────────────────────────────────────────────────

def title_card(game):
    """
    Opening card – big, warm, ceremonial.
    Shows: series name, game number, date, opponent, result.
    """
    img, draw = _blank()

    # Subtle gradient feel: darker stripe at top
    draw.rectangle([0, 0, W, 180], fill=CARD)

    # Crown / chess piece icon
    draw.text((W // 2, 130), '♛', font=font(96), fill=GOLD, anchor='mm')

    # Series name
    draw.text((W // 2, 230), "Aaron's Chess Journey", font=font(68), fill=TEXT, anchor='mm')

    # Game number – large and prominent
    draw.text((W // 2, 360), f'Game #{game["game_number"]}', font=font(96), fill=GOLD, anchor='mm')

    # Date + opponent
    opponent_line = f'{game["date"]}  ·  vs {game["opponent"]}'
    draw.text((W // 2, 480), opponent_line, font=font(42), fill=MUTED, anchor='mm')

    # Opening
    opening = game.get('opening', '')
    if opening:
        draw.text((W // 2, 550), opening, font=font(34), fill=MUTED, anchor='mm')

    # Result badge – centred
    result = game.get('result', 'draw')
    mapping = {'win': ('  W I N  ', GREEN), 'loss': ('  L O S S  ', RED), 'draw': ('  D R A W  ', AMBER)}
    label, color = mapping.get(result, ('  ?  ', MUTED))
    f36 = font(44)
    bbox = f36.getbbox(label)
    bw = bbox[2] - bbox[0] + 60
    bh = bbox[3] - bbox[1] + 30
    bx = (W - bw) // 2
    by = 640
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=bh // 2, fill=color)
    draw.text((W // 2, by + bh // 2), label, font=f36, fill=BG, anchor='mm')

    # Time + steps
    meta = f'{game["time_str"]}  ·  {game["steps"]} 步'
    draw.text((W // 2, 760), meta, font=font(32), fill=MUTED, anchor='mm')

    # Bottom stripe
    draw.rectangle([0, H - 6, W, H], fill=GOLD)

    return img


def overview_card(game, board_img):
    """
    Board + game overview.
    Board at starting position (or after first few moves), overview text on right.
    """
    img, draw = _blank()
    _left_panel_bg(draw)
    _logo_text(draw)
    _series_label(draw, game['game_number'])
    _place_board(img, board_img)

    # Right panel
    y = 120

    draw.text((RIGHT_X, y), '今天的对局', font=font(22), fill=MUTED)
    y += 42

    # Players
    white = game['white_player']
    black = game['black_player']
    wrating = f" ({game['white_rating']})" if game.get('white_rating') else ''
    brating = f" ({game['black_rating']})" if game.get('black_rating') else ''

    draw.text((RIGHT_X, y), f'⚪ {white}{wrating}', font=font(34), fill=TEXT)
    y += 50
    draw.text((RIGHT_X, y), f'⚫ {black}{brating}', font=font(34), fill=TEXT)
    y += 70

    _divider(draw, y)
    y += 30

    # Opening
    opening = game.get('opening', '')
    if opening:
        draw.text((RIGHT_X, y), '开局', font=font(22), fill=MUTED)
        y += 34
        for line in _wrap(opening, 30):
            draw.text((RIGHT_X, y), line, font=font(36), fill=GOLD)
            y += 48
        y += 16

    _divider(draw, y)
    y += 30

    # Time + steps
    draw.text((RIGHT_X, y), f'⏱  {game["time_str"]}   ·   ♟ {game["steps"]} 步',
              font=font(32), fill=MUTED)
    y += 60

    # Result
    _result_badge(draw, game['result'], RIGHT_X, y, font(40))
    y += 80

    # Summary (first sentence)
    summary = game.get('summary', '')
    if summary:
        y += 10
        _divider(draw, y)
        y += 24
        for line in _wrap(summary, 26)[:4]:
            draw.text((RIGHT_X, y), line, font=font(30), fill=MUTED)
            y += 42

    draw.rectangle([0, H - 6, W, H], fill=GOLD)
    return img


def highlight_card(game, highlight, board_img):
    """
    Celebrate a good move Aaron made.
    Board with gold arrow on the left, encouragement on the right.
    """
    img, draw = _blank()
    _left_panel_bg(draw)
    _logo_text(draw)
    _series_label(draw, game['game_number'])
    _place_board(img, board_img)

    y = 120
    draw.text((RIGHT_X, y), '★  精彩时刻', font=font(22), fill=GOLD)
    y += 50

    step_label = f'第 {highlight["step"]} 步  {highlight["san"]}'
    draw.text((RIGHT_X, y), step_label, font=font(54), fill=GOLD)
    y += 80

    _divider(draw, y)
    y += 36

    # Description
    for line in _wrap(highlight.get('desc', ''), 24):
        draw.text((RIGHT_X, y), line, font=font(40), fill=TEXT)
        y += 56

    y += 30
    _divider(draw, y)
    y += 36

    # Encouragement
    draw.text((RIGHT_X, y), '就是这样，Aaron！', font=font(38), fill=GREEN)
    y += 54
    draw.text((RIGHT_X, y), '好棋是练出来的 ♟', font=font(32), fill=MUTED)

    draw.rectangle([0, H - 6, W, H], fill=GREEN)
    return img


def blunder_before_card(game, blunder, board_img, lesson_num, total_lessons):
    """
    Show the position BEFORE the mistake.
    Prompt: 'Aaron, what would you play here?'
    """
    img, draw = _blank()
    _left_panel_bg(draw)
    _logo_text(draw)
    _series_label(draw, game['game_number'])
    _place_board(img, board_img)

    y = 120
    draw.text((RIGHT_X, y), f'课程 {lesson_num} / {total_lessons}', font=font(22), fill=MUTED)
    y += 50

    draw.text((RIGHT_X, y), f'第 {blunder["step"]} 步', font=font(52), fill=TEXT)
    y += 72

    draw.text((RIGHT_X, y), '如果是你，会怎么走？', font=font(36), fill=MUTED)
    y += 64

    _divider(draw, y)
    y += 36

    # What Aaron played
    draw.text((RIGHT_X, y), 'Aaron 走了：', font=font(28), fill=MUTED)
    y += 40
    draw.text((RIGHT_X, y), blunder['san'], font=font(64), fill=RED)
    y += 80

    # Eval drop
    if blunder['drop'] > 0:
        draw.text((RIGHT_X, y), f'评估下跌  ▼ {blunder["drop"]:.2f} 兵', font=font(32), fill=RED)
        y += 50

    blunder_label = '昏着 BLUNDER' if blunder['type'] == 'blunder' else '失误 MISTAKE'
    _badge(draw, RIGHT_X, y, f'  {blunder_label}  ',
           RED if blunder['type'] == 'blunder' else AMBER,
           fnt=font(28))

    draw.rectangle([0, H - 6, W, H], fill=RED)
    return img


def blunder_after_card(game, blunder, board_img, lesson_num, total_lessons):
    """
    Show the BETTER move with explanation.
    Warm and instructive, not harsh.
    """
    img, draw = _blank()
    _left_panel_bg(draw)
    _logo_text(draw)
    _series_label(draw, game['game_number'])
    _place_board(img, board_img)

    y = 120
    draw.text((RIGHT_X, y), f'课程 {lesson_num} / {total_lessons}', font=font(22), fill=MUTED)
    y += 50

    draw.text((RIGHT_X, y), '更好的走法是…', font=font(38), fill=MUTED)
    y += 60

    draw.text((RIGHT_X, y), blunder.get('best', '?'), font=font(72), fill=GREEN)
    y += 90

    _divider(draw, y)
    y += 36

    reason = blunder.get('reason', '')
    if reason:
        draw.text((RIGHT_X, y), '原因：', font=font(28), fill=MUTED)
        y += 40
        for line in _wrap(reason, 24):
            draw.text((RIGHT_X, y), line, font=font(34), fill=TEXT)
            y += 48
        y += 16

    _divider(draw, y)
    y += 30

    draw.text((RIGHT_X, y), '每次犯错都是一次成长 ♟', font=font(32), fill=GOLD)

    draw.rectangle([0, H - 6, W, H], fill=GREEN)
    return img


def lesson_card(game):
    """
    Final card – today's takeaways.
    Warm, encouraging, memorable.
    """
    img, draw = _blank()

    # Subtle top bar
    draw.rectangle([0, 0, W, 10], fill=GOLD)

    # Icon
    draw.text((W // 2, 160), '♟', font=font(72), fill=GOLD, anchor='mm')

    draw.text((W // 2, 260), "Aaron's Chess Journey", font=font(48), fill=MUTED, anchor='mm')
    draw.text((W // 2, 330), f'Game #{game["game_number"]}  ·  Today I learned…',
              font=font(36), fill=GOLD, anchor='mm')

    y = 420
    lessons = game.get('lessons', [])
    if not lessons:
        lessons = ['每盘棋都是进步的机会']

    for i, lesson in enumerate(lessons[:3], 1):
        # Bullet circle
        draw.ellipse([W // 2 - 380 - 18, y + 2, W // 2 - 380 + 18, y + 40],
                     fill=GOLD)
        draw.text((W // 2 - 380, y + 20), str(i), font=font(22), fill=BG, anchor='mm')
        # Lesson text
        lesson_lines = _wrap(lesson, 30)
        for line in lesson_lines:
            draw.text((W // 2 - 350, y), line, font=font(36), fill=TEXT)
            y += 48
        y += 20

    # Bottom motivational line
    draw.text((W // 2, H - 120), '下棋不复盘 = 没下过   Keep going, Aaron!',
              font=font(30), fill=MUTED, anchor='mm')

    # Date
    draw.text((W // 2, H - 70), game.get('date', ''), font=font(26), fill=BORDER, anchor='mm')

    draw.rectangle([0, H - 6, W, H], fill=GOLD)
    return img
