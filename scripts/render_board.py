#!/usr/bin/env python3
"""Render a chess board as a PIL Image from FEN or move list."""

from PIL import Image, ImageDraw, ImageFont
import chess
import math

SQUARE_SIZE = 60
BOARD_PX    = SQUARE_SIZE * 8   # 480
COORD_MARGIN = 24  # pixels reserved for rank/file labels

# Chess.com green theme
LIGHT_SQ  = (238, 238, 210)
DARK_SQ   = (118, 150,  86)
HL_LIGHT  = (205, 210, 106)   # last-move highlight on light square
HL_DARK   = (170, 162,  58)   # last-move highlight on dark square

PIECE_FONT = '/Library/Fonts/Arial Unicode.ttf'

# Unicode pieces – same glyph set but we colour them differently
PIECE_CHARS = {
    (chess.PAWN,   chess.WHITE): '♙',
    (chess.KNIGHT, chess.WHITE): '♘',
    (chess.BISHOP, chess.WHITE): '♗',
    (chess.ROOK,   chess.WHITE): '♖',
    (chess.QUEEN,  chess.WHITE): '♕',
    (chess.KING,   chess.WHITE): '♔',
    (chess.PAWN,   chess.BLACK): '♟',
    (chess.KNIGHT, chess.BLACK): '♞',
    (chess.BISHOP, chess.BLACK): '♝',
    (chess.ROOK,   chess.BLACK): '♜',
    (chess.QUEEN,  chess.BLACK): '♛',
    (chess.KING,   chess.BLACK): '♚',
}

WHITE_PIECE_COLOR = (255, 255, 255)
BLACK_PIECE_COLOR = ( 20,  20,  20)
WHITE_OUTLINE     = ( 50,  50,  50)
BLACK_OUTLINE     = (200, 200, 200)

COORD_COLOR     = (110, 110, 110)
COORD_FONT_SIZE = 13


def _draw_coords(img, flipped=False):
    """Draw a-h file labels at bottom and 1-8 rank labels on left (chess.com style)."""
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(PIECE_FONT, COORD_FONT_SIZE)
    except Exception:
        font = ImageFont.load_default()

    # File labels (a-h) at bottom, below the board
    for f in range(8):
        col = f if not flipped else 7 - f
        x = col * SQUARE_SIZE + COORD_MARGIN + SQUARE_SIZE // 2
        y = BOARD_PX + COORD_MARGIN + 6
        label = chr(ord('a') + f)
        draw.text((x, y), label, font=font, anchor='mt', fill=COORD_COLOR)

    # Rank labels (1-8) on left, inside left column
    for r in range(8):
        row = 7 - r if not flipped else r
        x = COORD_MARGIN - 6
        y = row * SQUARE_SIZE + COORD_MARGIN + SQUARE_SIZE // 2
        label = str(r + 1)
        draw.text((x, y), label, font=font, anchor='rm', fill=COORD_COLOR)


def _sq_center(sq, flipped=False):
    """Return pixel (cx, cy) for the center of a square (accounting for coord margin)."""
    f = chess.square_file(sq)
    r = chess.square_rank(sq)
    if flipped:
        col = 7 - f
        row = r
    else:
        col = f
        row = 7 - r
    return (col * SQUARE_SIZE + COORD_MARGIN + SQUARE_SIZE // 2,
            row * SQUARE_SIZE + COORD_MARGIN + SQUARE_SIZE // 2)


def _sq_rect(sq, flipped=False):
    """Return [x1,y1,x2,y2] rect for a square (accounting for coord margin)."""
    cx, cy = _sq_center(sq, flipped)
    half = SQUARE_SIZE // 2
    return [cx - half, cy - half, cx + half, cy + half]


def _draw_arrow(draw, from_sq, to_sq, color, flipped=False, alpha=200):
    """Draw a filled arrow from one square to another."""
    fx, fy = _sq_center(from_sq, flipped)
    tx, ty = _sq_center(to_sq, flipped)

    dx, dy = tx - fx, ty - fy
    length = math.hypot(dx, dy)
    if length == 0:
        return

    # Unit vector
    ux, uy = dx / length, dy / length
    # Perpendicular
    px, py = -uy, ux

    shaft_w = SQUARE_SIZE * 0.18
    head_w  = SQUARE_SIZE * 0.40
    head_len = SQUARE_SIZE * 0.45

    # Shaft start/end (stop before arrowhead)
    shaft_end_x = tx - ux * head_len
    shaft_end_y = ty - uy * head_len

    # Shaft polygon (rectangle)
    shaft = [
        (fx + px * shaft_w,  fy + py * shaft_w),
        (fx - px * shaft_w,  fy - py * shaft_w),
        (shaft_end_x - px * shaft_w, shaft_end_y - py * shaft_w),
        (shaft_end_x + px * shaft_w, shaft_end_y + py * shaft_w),
    ]
    # Arrowhead triangle
    head = [
        (shaft_end_x + px * head_w, shaft_end_y + py * head_w),
        (shaft_end_x - px * head_w, shaft_end_y - py * head_w),
        (tx, ty),
    ]

    rgba = color + (alpha,)
    draw.polygon(shaft, fill=rgba)
    draw.polygon(head,  fill=rgba)


def draw_board(fen=None, moves=None, move_index=None,
               flipped=False, arrows=None, highlight_last=True):
    """
    Render a chess board.

    Args:
        fen:          FEN string (takes priority over moves)
        moves:        list of SAN strings; replayed up to move_index
        move_index:   how many moves to replay (None = all)
        flipped:      True to show from Black's perspective
        arrows:       list of (from_sq, to_sq, color_rgb) tuples
        highlight_last: shade the last-move squares

    Returns:
        PIL Image (BOARD_PX × BOARD_PX)
    """
    # Build board state
    board = chess.Board()
    last_move = None

    if fen:
        try:
            board = chess.Board(fen)
        except Exception:
            board = chess.Board()
    elif moves:
        n = move_index if move_index is not None else len(moves)
        for i, san in enumerate(moves[:n]):
            try:
                mv = board.parse_san(san)
                last_move = mv
                board.push(mv)
            except Exception:
                break

    # Create RGBA image so we can composite semi-transparent arrows
    # Add COORD_MARGIN to both dimensions to accommodate labels
    img_w = BOARD_PX + COORD_MARGIN
    img_h = BOARD_PX + COORD_MARGIN
    img   = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 255))
    base  = ImageDraw.Draw(img)

    # Draw squares
    for sq in chess.SQUARES:
        f, r = chess.square_file(sq), chess.square_rank(sq)
        is_light = (f + r) % 2 == 1
        rect = _sq_rect(sq, flipped)

        # Last-move highlight
        if highlight_last and last_move and sq in (last_move.from_square, last_move.to_square):
            color = HL_LIGHT if is_light else HL_DARK
        else:
            color = LIGHT_SQ if is_light else DARK_SQ

        base.rectangle(rect, fill=color)

    # Draw pieces
    try:
        piece_font = ImageFont.truetype(PIECE_FONT, int(SQUARE_SIZE * 0.82))
    except Exception:
        piece_font = ImageFont.load_default()

    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if not piece:
            continue
        cx, cy = _sq_center(sq, flipped)
        char = PIECE_CHARS.get((piece.piece_type, piece.color), '?')
        fill    = WHITE_PIECE_COLOR if piece.color == chess.WHITE else BLACK_PIECE_COLOR
        outline = WHITE_OUTLINE     if piece.color == chess.WHITE else BLACK_OUTLINE

        # Draw outline (slight offset trick for legibility)
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            base.text((cx + ox, cy + oy), char, font=piece_font,
                      anchor='mm', fill=outline)
        base.text((cx, cy), char, font=piece_font, anchor='mm', fill=fill)

    # Draw arrows on a separate transparent layer
    if arrows:
        arrow_layer = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))
        adraw = ImageDraw.Draw(arrow_layer)
        for from_sq, to_sq, color in arrows:
            _draw_arrow(adraw, from_sq, to_sq, color, flipped)
        img = Image.alpha_composite(img, arrow_layer)

    _draw_coords(img, flipped)

    return img.convert('RGB')


def board_at_move(moves, move_index, flipped=False, arrows=None):
    """Convenience: render board after move_index moves have been played."""
    return draw_board(moves=moves, move_index=move_index,
                      flipped=flipped, arrows=arrows)


def get_move_squares(board_before_fen, san):
    """Return (from_sq, to_sq) for a SAN move played on board_before_fen."""
    try:
        board = chess.Board(board_before_fen)
        mv = board.parse_san(san)
        return mv.from_square, mv.to_square
    except Exception:
        return None, None


def replay_to(moves, n):
    """Return FEN after n moves have been played."""
    board = chess.Board()
    for san in moves[:n]:
        try:
            board.push(board.parse_san(san))
        except Exception:
            break
    return board.fen()


if __name__ == '__main__':
    # Quick smoke test
    img = draw_board()
    img.save('/tmp/board_test.png')
    print('Board saved to /tmp/board_test.png')
