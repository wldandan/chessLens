#!/usr/bin/env python3
"""
Parse a chess review markdown file into structured data for video generation.

Handles two formats:
  OLD – has ## 📊 棋局概览 / ## ⚠️ 关键失误 / ## 🌟 今日收获 / ## 附录
  NEW – has bold **Opening:** header block / ## 📈 局面评估走势 / ## 🎯 关键收获
"""

import os
import re

AARON = 'aaronwang2026'

TIME_MAP = {
    60: '1分钟', 120: '2分钟', 180: '3分钟', 300: '5分钟',
    600: '10分钟', 900: '15分钟', 1800: '30分钟', 2700: '45分钟',
}


def _fmt_time(tc):
    if not tc or tc == '-':
        return tc or ''
    if '+' in tc:
        base, inc = tc.split('+', 1)
        secs = int(base) if base.isdigit() else 0
        mins = secs // 60 if secs >= 60 else secs
        return f"{mins}+{inc}" if inc != '0' else f"{mins}分钟"
    if tc.isdigit():
        secs = int(tc)
        return TIME_MAP.get(secs, f"{secs // 60}分钟" if secs >= 60 else f"{secs}秒")
    return tc


def _clean(text):
    """Remove markdown bold markers."""
    return re.sub(r'\*\*(.+?)\*\*', r'\1', text).strip()


def _section(content, header_re):
    """Return text from a section header until the next ## header."""
    m = re.search(header_re, content, re.MULTILINE)
    if not m:
        return ''
    start = m.end()
    nxt = re.search(r'^##\s', content[start:], re.MULTILINE)
    end = start + nxt.start() if nxt else len(content)
    return content[start:end].strip()


# ── Format detection ──────────────────────────────────────────────────────────

def _is_new_format(content):
    """True if the file uses the newer condensed format (bold header block)."""
    return bool(re.search(r'^\*\*Opening:\*\*', content, re.MULTILINE))


# ── OLD FORMAT parsers ────────────────────────────────────────────────────────

def _old_overview(content):
    sec = _section(content, r'^##\s.*棋局概览')
    info = {}
    for line in sec.splitlines():
        if '**执白**' in line:
            val = re.split(r'[：:]', line, 1)[-1].strip()
            m = re.match(r'(.+?)（(\d+)）', val)
            info['white_player'] = m.group(1).strip() if m else val
            info['white_rating'] = m.group(2) if m else ''
        elif '**执黑**' in line:
            val = re.split(r'[：:]', line, 1)[-1].strip()
            m = re.match(r'(.+?)（(\d+)）', val)
            info['black_player'] = m.group(1).strip() if m else val
            info['black_rating'] = m.group(2) if m else ''
        elif '开局' in line and ('：' in line or ':' in line):
            info['opening'] = re.split(r'[：:]', line, 1)[-1].strip()
        elif '总回合数' in line and ('：' in line or ':' in line):
            val = re.split(r'[：:]', line, 1)[-1].strip()
            info['steps'] = val.replace('步', '').strip()
    return info


def _old_highlights(content, aaron_color=None):
    sec = _section(content, r'^##\s.*亮点时刻')
    highlights = []
    color_cn = '白' if aaron_color == 'white' else '黑'
    for line in sec.splitlines():
        line = line.strip()
        # Format A: - **第18步（黑）** — Nxe4（...）
        m = re.match(
            r'-\s*\*\*第\s*(\d+)\s*步[（(]([白黑])[)）][^*]*\*\*\s*[—\-–]+\s*([A-Za-z0-9O][A-Za-z0-9+#=x\-]*)',
            line)
        if m:
            if aaron_color and m.group(2) != color_cn:
                continue
            highlights.append({
                'step': int(m.group(1)),
                'san':  m.group(3).strip(),
                'desc': '走出了好棋！',
            })
            continue
        # Format B: - **14.白** — Ke1（...）
        m2 = re.match(
            r'-\s*\*\*(\d+)\.([白黑])\*\*\s*[—\-–]+\s*([A-Za-z0-9O][A-Za-z0-9+#=x\-]*)',
            line)
        if m2:
            if aaron_color and m2.group(2) != color_cn:
                continue
            highlights.append({
                'step': int(m2.group(1)),
                'san':  m2.group(3).strip(),
                'desc': '走出了好棋！',
            })
            continue
        # Format C (original): - **第18步 Nxe4** — desc
        m3 = re.match(
            r'-\s*\*\*第\s*(\d+)\s*步\s+([A-Za-z0-9O+#=x\-]+)\*\*\s*[—\-–]+\s*(.+)',
            line)
        if m3:
            highlights.append({
                'step': int(m3.group(1)),
                'san':  m3.group(2).strip(),
                'desc': _clean(m3.group(3)),
            })
    return highlights


def _old_blunders(content, aaron_color=None):
    sec = _section(content, r'^##\s.*关键失误')
    blunders, current = [], None
    color_cn = '白' if aaron_color == 'white' else '黑'
    for line in sec.splitlines():
        line = line.strip()
        # Format A: 1. **第7步（黑）** — 💥 **BLUNDER**（跌 1.23 兵）
        m = re.match(r'\d+\.\s*\*\*第\s*(\d+)\s*步[（(]([白黑])[)）][^*]*\*\*', line)
        if m:
            if aaron_color and m.group(2) != color_cn:
                current = None
                continue
            drop_m = re.search(r'跌\s*([0-9.]+)\s*兵', line)
            current = {
                'step': int(m.group(1)), 'san': '',
                'drop': float(drop_m.group(1)) if drop_m else 0.0,
                'best': '', 'reason': '',
                'type': 'blunder' if '💥' in line or 'BLUNDER' in line else 'mistake',
            }
            blunders.append(current)
            continue
        # Format B (original): 1. **第7步 san**
        m2 = re.match(r'\d+\.\s*\*\*第\s*(\d+)\s*步\s+([A-Za-z0-9O+#=x\-]+)\*\*', line)
        if m2:
            current = {
                'step': int(m2.group(1)), 'san': m2.group(2).strip(),
                'drop': 0.0, 'best': '', 'reason': '',
                'type': 'blunder' if '💥' in line or 'BLUNDER' in line else 'mistake',
            }
            blunders.append(current)
            continue
        if current:
            # SAN from backtick: - 走了 `Bb6`
            ms = re.search(r'走了\s*`([A-Za-z0-9O][A-Za-z0-9+#=x\-]*)`', line)
            if ms and not current['san']:
                current['san'] = ms.group(1).strip()
            md = re.search(r'跌\s*\*\*([0-9.]+)\s*兵\*\*', line)
            if md:
                current['drop'] = float(md.group(1))
            mb = re.search(r'推荐着法[：:]\s*`([^`]+)`', line)
            if mb:
                current['best'] = mb.group(1).strip()
            mr = re.search(r'(?:失误分析|原因)[：:]\s*(.+)', line)
            if mr:
                current['reason'] = _clean(mr.group(1))
    # Drop blunders with no SAN
    return [b for b in blunders if b['san']]


def _old_lessons(content):
    sec = _section(content, r'^##\s.*今日收获')
    lessons = []
    for line in sec.splitlines():
        m = re.match(r'^[\d]+\.\s+(.+)', line.strip()) or re.match(r'^-\s+(.+)', line.strip())
        if m:
            lessons.append(_clean(m.group(1)))
    return lessons[:3]


def _old_moves(content):
    """Extract SAN list from 5-column appendix table (old format)."""
    sec = _section(content, r'^##\s.*附录')
    if not sec:
        return []
    rows = []
    for line in sec.splitlines():
        m = re.match(
            r'\|\s*(\d+)\.(白|黑)\s*\|\s*([A-Za-z0-9O][A-Za-z0-9+#=x\-]*)\s*\|',
            line.strip())
        if m:
            rows.append((int(m.group(1)), m.group(2), m.group(3).strip()))
    rows.sort(key=lambda r: (r[0], 0 if r[1] == '白' else 1))
    return [r[2] for r in rows]


# ── NEW FORMAT parsers ────────────────────────────────────────────────────────

def _new_header(content):
    """Parse the bold metadata block at the top of new-format files."""
    info = {}
    for line in content.splitlines()[:20]:
        m = re.match(r'\*\*Opening:\*\*\s*(.+)', line.strip())
        if m:
            info['opening'] = m.group(1).strip()
        m2 = re.match(r'\*\*Rating:\*\*\s*(.+)', line.strip())
        if m2:
            raw = m2.group(1).strip()
            # e.g. "aaronwang2026(1441) vs limjp77(1446)"
            parts = re.findall(r'(\w+)\((\d+)\)', raw)
            for name, rating in parts:
                if name == AARON or 'aaron' in name.lower():
                    info['aaron_rating'] = rating
                else:
                    info['opp_rating'] = rating
    return info


def _new_moves(content):
    """Extract moves from 4-column evaluation table (new format).
    Skips grouped rows like '9–13.白 | (多步失误)'.
    """
    sec = _section(content, r'^##\s.*局面评估走势')
    if not sec:
        return []
    rows = []
    for line in sec.splitlines():
        # Only match single-move rows (not ranges like 9–13)
        m = re.match(
            r'\|[\s\*]*(\d+)\.(白|黑)[\s\*]*\|[\s\*]*([A-Za-z0-9O][A-Za-z0-9+#=x\-]*)[\s\*]*\|',
            line.strip())
        if m:
            rows.append((int(m.group(1)), m.group(2), m.group(3).strip()))
    rows.sort(key=lambda r: (r[0], 0 if r[1] == '白' else 1))
    return [r[2] for r in rows]


def _new_highlights_from_table(content, aaron_color):
    """Find Aaron's good moves from the evaluation table (new format)."""
    sec = _section(content, r'^##\s.*局面评估走势')
    highlights = []
    color_cn = '白' if aaron_color == 'white' else '黑'
    for line in sec.splitlines():
        m = re.match(
            r'\|[\s\*]*(\d+)\.(白|黑)[\s\*]*\|[\s\*]*([A-Za-z0-9O][A-Za-z0-9+#=x\-]*)[\s\*]*\|.*?(妙手|好棋)',
            line.strip())
        if m and m.group(2) == color_cn:
            highlights.append({
                'step': int(m.group(1)),
                'san':  m.group(3).strip(),
                'desc': '走出了好棋！',
            })
    return highlights[:2]


def _new_blunders_from_table(content, aaron_color):
    """Find Aaron's blunders/mistakes from the evaluation table (new format)."""
    sec = _section(content, r'^##\s.*局面评估走势')
    blunders = []
    color_cn = '白' if aaron_color == 'white' else '黑'
    for line in sec.splitlines():
        m = re.match(
            r'\|[\s\*]*(\d+)\.(白|黑)[\s\*]*\|[\s\*]*([A-Za-z0-9O][A-Za-z0-9+#=x\-]*)[\s\*]*\|'
            r'[\s\*💥⚠🟡🔴⚖👑🟢💀\+\-0-9.]*\|[\s\*]*([^|]*)',
            line.strip())
        if m and m.group(2) == color_cn:
            trend = m.group(4)
            is_blunder = '昏着' in trend or '💥' in trend
            is_mistake = '失误' in trend or '⚠️' in trend
            if is_blunder or is_mistake:
                blunders.append({
                    'step': int(m.group(1)),
                    'san':  m.group(3).strip(),
                    'drop': 0.0,
                    'best': '',
                    'reason': '',
                    'type': 'blunder' if is_blunder else 'mistake',
                })
    return blunders[:3]


def _new_lessons(content):
    sec = _section(content, r'^##\s.*关键收获')
    lessons = []
    for line in sec.splitlines():
        m = re.match(r'^[\d]+\.\s+(.+)', line.strip()) or re.match(r'^-\s+(.+)', line.strip())
        if m:
            lessons.append(_clean(m.group(1)))
    return lessons[:3]


def _parse_fens(content):
    """Extract named FEN positions from either format.
    Only accepts strings that look like real FENs (contain '/' board separator).
    """
    fens = {}
    for m in re.finditer(r'第\s*(\d+)\s*步[^`\n]*`([^`]+)`', content):
        step = int(m.group(1))
        candidate = m.group(2).strip()
        if '/' in candidate and len(candidate) > 20:   # real FEN check
            fens[step] = candidate
    return fens


def _parse_summary(content):
    sec = _section(content, r'^##\s*总体评价')
    paras = [p.strip() for p in sec.split('\n\n') if p.strip()]
    return paras[0] if paras else ''


# ── Main parse function ───────────────────────────────────────────────────────

def parse(filepath, docs_dir=None):
    """Return a dict with all game data needed by the video generator."""
    filename = os.path.basename(filepath)
    parts    = filename.replace('.md', '').split('_')

    date       = parts[0] if len(parts) > 0 else ''
    game_id    = parts[1] if len(parts) > 1 else ''
    file_white = parts[2] if len(parts) > 2 else ''
    color_res  = parts[3] if len(parts) > 3 else ''
    file_black = parts[4] if len(parts) > 4 else ''
    steps_raw  = parts[5] if len(parts) > 5 else ''
    time_raw   = parts[6] if len(parts) > 6 else ''

    # Aaron's color & opponent
    if file_white == AARON:
        aaron_is_white = '执白' in color_res
        opponent = file_black
    else:
        aaron_is_white = False
        opponent = file_white

    # Result from Aaron's perspective
    if file_white == AARON:
        result = 'win' if '胜' in color_res else ('draw' if '和' in color_res else 'loss')
    else:
        result = 'loss' if '胜' in color_res else ('draw' if '和' in color_res else 'win')

    aaron_color = 'white' if aaron_is_white else 'black'

    with open(filepath, encoding='utf-8') as f:
        content = f.read()

    new_fmt = _is_new_format(content)

    if new_fmt:
        hdr       = _new_header(content)
        opening   = hdr.get('opening', '')
        highlights = _new_highlights_from_table(content, aaron_color)
        blunders   = _new_blunders_from_table(content, aaron_color)
        lessons    = _new_lessons(content)
        moves      = _new_moves(content)
        white_rating = hdr.get('aaron_rating', '') if aaron_is_white else hdr.get('opp_rating', '')
        black_rating = hdr.get('opp_rating', '')   if aaron_is_white else hdr.get('aaron_rating', '')
        steps = steps_raw.replace('步', '')
        summary = ''
    else:
        ov         = _old_overview(content)
        opening    = ov.get('opening', '')
        highlights = _old_highlights(content, aaron_color)
        blunders   = _old_blunders(content, aaron_color)
        lessons    = _old_lessons(content)
        moves      = _old_moves(content)
        white_rating = ov.get('white_rating', '')
        black_rating = ov.get('black_rating', '')
        steps = ov.get('steps', steps_raw.replace('步', ''))
        summary = _parse_summary(content)

    fens = _parse_fens(content)

    # Game number (1-based, sorted by filename)
    game_number = 1
    if docs_dir and os.path.isdir(docs_dir):
        all_files = sorted(f for f in os.listdir(docs_dir) if f.endswith('.md'))
        if filename in all_files:
            game_number = all_files.index(filename) + 1

    return {
        'filename':       filename,
        'date':           date,
        'game_id':        game_id,
        'game_number':    game_number,
        'white_player':   file_white,
        'black_player':   file_black,
        'white_rating':   white_rating,
        'black_rating':   black_rating,
        'aaron_is_white': aaron_is_white,
        'aaron_color':    aaron_color,
        'opponent':       opponent,
        'result':         result,
        'steps':          steps,
        'time_str':       _fmt_time(time_raw),
        'opening':        opening,
        'summary':        summary,
        'highlights':     highlights,
        'blunders':       blunders,
        'lessons':        lessons,
        'moves':          moves,
        'fens':           fens,   # {step_number: fen_string}
        'format':         'new' if new_fmt else 'old',
    }


if __name__ == '__main__':
    import sys, json
    data = parse(sys.argv[1], docs_dir=os.path.dirname(sys.argv[1]))
    data.pop('moves')
    print(json.dumps(data, ensure_ascii=False, indent=2))
