#!/usr/bin/env python3
"""
make_video.py – Aaron's Chess Journey video generator.

Usage:
    python3 scripts/make_video.py docs/2026-05-10_..._limjp77_23步_600.md
    python3 scripts/make_video.py docs/  # batch: all files in docs/

Output: videos/{game_filename}.mp4
"""

import os
import sys
import subprocess
import tempfile
import shutil
import chess

# Make sure scripts/ is importable regardless of cwd
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

from parse_review  import parse
from render_board  import draw_board, replay_to, get_move_squares, board_at_move
from make_cards    import (title_card, overview_card, highlight_card,
                           blunder_before_card, blunder_after_card, lesson_card)

DOCS_DIR   = os.path.join(os.path.dirname(SCRIPTS_DIR), 'docs')
VIDEOS_DIR = os.path.join(os.path.dirname(SCRIPTS_DIR), 'videos')

# Arrow colours (RGB, alpha added in render_board)
ARROW_GOLD  = (230, 184,   0)   # highlight / good move
ARROW_RED   = (220,  50,  50)   # mistake played
ARROW_GREEN = ( 50, 200, 100)   # recommended best move

# Seconds each card stays on screen
CARD_DURATIONS = {
    'title':           5,
    'overview':        5,
    'highlight':       6,
    'blunder_before':  6,
    'blunder_after':   6,
    'lesson':          7,
}


# ── Board helpers ─────────────────────────────────────────────────────────────

def _flipped(game):
    return not game['aaron_is_white']


def _board_at(game, move_index, arrows=None):
    return draw_board(moves=game['moves'], move_index=move_index,
                      flipped=_flipped(game), arrows=arrows)


def _arrows_for_move(game, move_index):
    """Return arrow list highlighting the move at position move_index."""
    if not game['moves'] or move_index <= 0:
        return []
    fen_before = replay_to(game['moves'], move_index - 1)
    san = game['moves'][move_index - 1]
    from_sq, to_sq = get_move_squares(fen_before, san)
    if from_sq is None:
        return []
    return [(from_sq, to_sq, ARROW_RED)]


def _best_move_arrows(game, blunder):
    """Return green arrow for the recommended best move."""
    step = blunder['step']
    best = blunder.get('best', '')
    if not best or step <= 0 or not game['moves']:
        return []
    # The blunder is at move index (step*2 - 1 for white, step*2 for black)
    # Approximate: find the position by step number in the table
    # The move table has white then black, so white's move N is at index 2*(N-1)
    # For now, use the board state just before the blunder
    move_idx = _blunder_move_index(game, blunder)
    if move_idx is None:
        return []
    fen_before = replay_to(game['moves'], move_idx)
    from_sq, to_sq = get_move_squares(fen_before, best)
    if from_sq is None:
        return []
    return [(from_sq, to_sq, ARROW_GREEN)]


def _blunder_move_index(game, blunder):
    """Return the 0-based move list index just BEFORE the blunder move."""
    step = blunder['step']
    san  = blunder['san']
    moves = game['moves']
    # Search: the blunder san appears at a position close to step*2
    for i in range(max(0, (step - 1) * 2 - 2), min(len(moves), step * 2 + 2)):
        if moves[i] == san:
            return i   # index of the blunder move itself; board is replayed to i
    # Fallback: estimate position from step
    return min((step - 1) * 2, len(moves) - 1)


# ── Card sequence builder ──────────────────────────────────────────────────────

def build_cards(game):
    """
    Return list of (PIL Image, duration_seconds) tuples.
    Structure:
      1. Title card
      2. Overview (board at ~move 6 or start)
      3. Highlights (max 1)
      4. Blunders (max 2, each: before + after)
      5. Lesson card
    """
    cards = []
    flipped = _flipped(game)

    # ── 1. Title ───────────────────────────────────────────────────────────────
    cards.append((title_card(game), CARD_DURATIONS['title']))

    # ── 2. Overview – show board after ~6 moves (opening snapshot) ─────────────
    preview_idx = min(6, len(game['moves']))
    overview_board = _board_at(game, preview_idx)
    cards.append((overview_card(game, overview_board), CARD_DURATIONS['overview']))

    # ── 3. Best highlight (max 1) ──────────────────────────────────────────────
    for hl in game['highlights'][:1]:
        hl_idx = _blunder_move_index(game, {'step': hl['step'], 'san': hl['san']})
        fen_before = replay_to(game['moves'], hl_idx) if game['moves'] else None
        hl_from, hl_to = get_move_squares(fen_before, hl['san']) if fen_before else (None, None)
        hl_arrows = [(hl_from, hl_to, ARROW_GOLD)] if hl_from is not None else []
        hl_board = _board_at(game, hl_idx + 1, arrows=hl_arrows)
        cards.append((highlight_card(game, hl, hl_board), CARD_DURATIONS['highlight']))

    # ── 4. Blunders (max 2) ────────────────────────────────────────────────────
    top_blunders = sorted(game['blunders'], key=lambda b: b['drop'], reverse=True)[:2]
    total = len(top_blunders)

    for num, blunder in enumerate(top_blunders, 1):
        move_idx = _blunder_move_index(game, blunder)

        # Card A – position BEFORE the blunder, with red arrow showing what was played
        before_arrows = _arrows_for_move(game, move_idx + 1)
        board_before  = _board_at(game, move_idx, arrows=before_arrows)
        cards.append((blunder_before_card(game, blunder, board_before, num, total),
                      CARD_DURATIONS['blunder_before']))

        # Card B – same position but green arrow for best move
        best_arrows = _best_move_arrows(game, blunder)
        board_best  = _board_at(game, move_idx, arrows=best_arrows)
        cards.append((blunder_after_card(game, blunder, board_best, num, total),
                      CARD_DURATIONS['blunder_after']))

    # ── 5. Lesson card ─────────────────────────────────────────────────────────
    cards.append((lesson_card(game), CARD_DURATIONS['lesson']))

    return cards


# ── ffmpeg assembly ───────────────────────────────────────────────────────────

def assemble(frames, output_path):
    """
    frames: list of (path, duration) – PNG files + duration in seconds.
    Produces a 1920×1080 h264 mp4 with simple cut transitions.
    """
    n = len(frames)
    if n == 0:
        raise ValueError('No frames to assemble')

    # Build ffmpeg command using concat filter
    args = ['ffmpeg', '-y']
    for path, dur in frames:
        args += ['-loop', '1', '-t', str(dur), '-i', path]

    # Scale + setsar + fps each input, then concat
    scale_parts = '; '.join(
        f'[{i}:v]scale=1920:1080,setsar=1,fps=25,format=yuv420p[v{i}]'
        for i in range(n)
    )
    concat_in  = ''.join(f'[v{i}]' for i in range(n))
    concat_out = f'{concat_in}concat=n={n}:v=1:a=0[out]'
    filter_str = f'{scale_parts}; {concat_out}'

    args += [
        '-filter_complex', filter_str,
        '-map',    '[out]',
        '-c:v',    'libx264',
        '-preset', 'medium',
        '-crf',    '23',
        '-r',      '25',
        '-pix_fmt','yuv420p',
        output_path,
    ]

    print(f'  Running ffmpeg ({n} frames → {output_path})')
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        print('ffmpeg stderr:', result.stderr[-1000:])
        raise RuntimeError('ffmpeg failed')


# ── Main ──────────────────────────────────────────────────────────────────────

def make_video(md_path, output_dir=None):
    output_dir = output_dir or VIDEOS_DIR
    os.makedirs(output_dir, exist_ok=True)

    print(f'\n▶  Parsing  {os.path.basename(md_path)}')
    game = parse(md_path, docs_dir=DOCS_DIR)

    print(f'   Game #{game["game_number"]}  {game["date"]}  '
          f'vs {game["opponent"]}  →  {game["result"].upper()}')
    print(f'   Opening: {game["opening"] or "(unknown)"}')
    print(f'   Moves in table: {len(game["moves"])}  '
          f'Blunders: {len(game["blunders"])}  '
          f'Highlights: {len(game["highlights"])}')

    print('▶  Building cards…')
    cards = build_cards(game)
    print(f'   {len(cards)} cards total')

    # Save PNGs to a temp directory
    tmp = tempfile.mkdtemp(prefix='chessvid_')
    try:
        frames = []
        for i, (card_img, duration) in enumerate(cards):
            path = os.path.join(tmp, f'card_{i:03d}.png')
            card_img.save(path)
            frames.append((path, duration))
            print(f'   card {i+1}/{len(cards)} saved  ({duration}s)')

        stem = os.path.basename(md_path).replace('.md', '')
        out  = os.path.join(output_dir, f'{stem}.mp4')

        print('▶  Assembling video…')
        assemble(frames, out)
        print(f'✓  Video saved: {out}')
        return out

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    if len(sys.argv) < 2:
        print('Usage: python3 scripts/make_video.py <review.md | docs_dir/>')
        sys.exit(1)

    target = sys.argv[1]

    if os.path.isdir(target):
        # Batch mode
        files = sorted(f for f in os.listdir(target) if f.endswith('.md'))
        print(f'Batch mode: {len(files)} files in {target}')
        for f in files:
            try:
                make_video(os.path.join(target, f))
            except Exception as e:
                print(f'  ERROR {f}: {e}')
    elif os.path.isfile(target):
        make_video(target)
    else:
        print(f'Not found: {target}')
        sys.exit(1)


if __name__ == '__main__':
    main()
