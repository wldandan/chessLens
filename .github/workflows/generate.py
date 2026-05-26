#!/usr/bin/env python3
"""Generate static HTML site from markdown files."""

import os
import mistune
from datetime import datetime
import time

SRC_DIR = 'docs/reviews/docs'
OUTPUT_DIR = 'docs'

def get_md_files():
    """Get all markdown files in docs/ directory."""
    files = []
    if os.path.exists(SRC_DIR):
        for f in sorted(os.listdir(SRC_DIR)):
            if f.endswith('.md') and f != 'index.md':
                files.append(f)
    return files

def read_file(path):
    """Read file content."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def get_file_mtime(path):
    """Get file modification time formatted as YYYY-MM-DD HH:MM."""
    mtime = os.path.getmtime(path)
    return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')

def get_game_list():
    """Generate game list from markdown files."""
    import re
    games = []
    for f in get_md_files():
        # Filename format: {日期}_{game_id}_{白方}_{胜负}_{黑方}_{回合数}步}_{time_control}.md
        # Example: 2026-04-14_167293652644_aaronwang2026_执白胜_Clement924810_19步_10+0.md
        # Parts: ['2026-04-14', '167293652644', 'aaronwang2026', '执白胜', 'Clement924810', '19步', '10+0']
        basename = f.replace('.md', '')
        parts = basename.split('_')

        if len(parts) < 6:
            continue

        # Date is always at parts[0]
        date = parts[0]

        # Color and result from parts[3] (e.g., '执白胜', '执黑和')
        color_result = parts[3]
        color_text = '执白' if '执白' in color_result else '执黑'
        result = '胜' if '胜' in color_result else ('和' if '和' in color_result else '败')

        # Opponent: parts[4] 固定是对局中不在 parts[2] 的那方
        # 文件格式: {date}_{game_id}_{白方}_{color_result}_{黑方}_{steps}_{time}.md
        # 当 aaron 执黑时 parts[2]=对手(白), parts[4]=aaron; aaron 执白时 parts[2]=aaron, parts[4]=对手(黑)
        # 用 parts[2] 是否等于 'aaronwang2026' 来判断
        opponent = parts[2] if parts[2] != 'aaronwang2026' else parts[4]

        # Steps from parts[5] (e.g., "19步" -> "19")
        steps = parts[5].replace('步', '') if '步' in parts[5] else parts[5]

        # Time control from parts[6] if exists
        time_control_raw = parts[6] if len(parts) > 6 else '-'
        # Convert Lichess seconds format to human readable (e.g., "1800" -> "30+0", "900+10" -> "15+10")
        if '+' in time_control_raw:
            # Handle "900+10" format
            base, inc = time_control_raw.split('+')
            if base.isdigit():
                seconds = int(base)
                minutes = seconds // 60 if seconds >= 60 else seconds
                if inc == '0':
                    time_control = f"{minutes}分钟"
                else:
                    time_control = f"{minutes}分钟+{inc}秒"
            else:
                time_control = time_control_raw
        elif time_control_raw.isdigit():
            seconds = int(time_control_raw)
            if seconds >= 60:
                minutes = seconds // 60
                time_control = f"{minutes}分钟"
            else:
                time_control = time_control_raw
        else:
            time_control = time_control_raw

        content = read_file(os.path.join(SRC_DIR, f))

        # Count highlights: "- **" OR numbered items OR "### 🚨" (sub-headers in blunder sections)
        # Start on ## 🎯 (template) OR ## 💥 (alternative format for opponent analysis)
        # End when hitting ## ⚠️ (mistake section starts) OR --- OR ## 💡/🌟
        highlights = 0
        in_highlight = False
        in_blunder_section = False  # True when we're in ## 💥 section
        for line in content.split('\n'):
            stripped = line.strip()
            if (stripped.startswith('##') or stripped.startswith('###')) and '🎯' in stripped:
                in_highlight = True
                in_blunder_section = False
                continue
            if (stripped.startswith('##') or stripped.startswith('###')) and '💥' in stripped:
                in_highlight = True
                in_blunder_section = True
                continue
            if in_highlight:
                if in_blunder_section:
                    # In ## 💥 section: count ### 🚨 sub-headers as highlights
                    if stripped.startswith('### 🚨'):
                        highlights += 1
                else:
                    # In ## 🎯 section: count numbered or "- **" items
                    if stripped.startswith('- **') or (stripped and stripped[0].isdigit() and '. **' in stripped):
                        highlights += 1
            # End highlight section: --- OR ## 💡/🌟/📚 OR ## ⚠️ (mistakes section)
            if in_highlight and (
                stripped.startswith('---') or
                (('⚠️' in stripped or '💡' in stripped or '🌟' in stripped or '📚' in stripped) and ('##' in stripped or '###' in stripped))
            ):
                in_highlight = False
                in_blunder_section = False

        # Count mistakes: numbered items "1. **..." or table rows with 💥/💀/⚠️
        mistakes = 0
        in_mistake = False
        lines = content.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            if (stripped.startswith('##') or stripped.startswith('###')) and '⚠️' in stripped:
                in_mistake = True
                continue
            if in_mistake:
                is_numbered = (
                    (stripped.startswith('**') and len(stripped) > 3 and stripped[2].isdigit() and stripped[3] == '.') or
                    (stripped and stripped[0].isdigit() and '. **' in stripped)
                )
                is_bullet = stripped.startswith('- ')  # new format: "- 第 X 步（白）：..."
                is_table_blunder = stripped.startswith('|') and ('💥' in stripped or '💀' in stripped or '⚠️' in stripped)
                if is_numbered or is_bullet or is_table_blunder:
                    mistakes += 1
            if in_mistake and (
                stripped.startswith('---') or
                (('💡' in stripped or '🌟' in stripped or '📚' in stripped) and ('##' in stripped or '###' in stripped))
            ):
                if stripped.startswith('---'):
                    next_idx = i + 1
                    while next_idx < len(lines) and not lines[next_idx].strip():
                        next_idx += 1
                    if next_idx < len(lines):
                        next_line = lines[next_idx].strip()
                        next_is_numbered = (
                            (next_line.startswith('**') and len(next_line) > 3 and next_line[2].isdigit() and next_line[3] == '.') or
                            (next_line and next_line[0].isdigit() and '. **' in next_line)
                        )
                        if next_is_numbered:
                            continue
                in_mistake = False

        file_path = os.path.join(SRC_DIR, f)
        analyze_time = get_file_mtime(file_path)

        games.append({
            'date': date,
            'color': color_text,
            'result': result,
            'opponent': opponent,
            'steps': steps,
            'time_control': time_control,
            'highlights': highlights,
            'mistakes': mistakes,
            'filename': f,
            'analyze_time': analyze_time
        })
    return sorted(games, key=lambda x: x['date'], reverse=True)

INDEX_CSS = """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    :root {
        --bg-dark: #1a1a2e;
        --bg-card: #16213e;
        --accent-gold: #e6b800;
        --accent-green: #4ade80;
        --accent-red: #f87171;
        --text-light: #f1f5f9;
        --text-muted: #94a3b8;
        --border: #334155;
    }
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background: var(--bg-dark);
        color: var(--text-light);
        min-height: 100vh;
    }
    .container {
        max-width: 1000px;
        margin: 0 auto;
        padding: 3rem 2rem;
    }
    header {
        text-align: center;
        margin-bottom: 4rem;
    }
    header::before {
        content: '♔';
        font-size: 4rem;
        color: var(--accent-gold);
        display: block;
        margin-bottom: 1rem;
        text-shadow: 0 0 30px rgba(230, 184, 0, 0.5);
    }
    .brand-name {
        font-size: 3.5rem;
        font-weight: 700;
        letter-spacing: 0.15em;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .slogan {
        font-size: 1.25rem;
        color: var(--text-muted);
        font-weight: 500;
        letter-spacing: 0.1em;
        margin-bottom: 1.5rem;
    }
    .ai-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem 1.25rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        letter-spacing: 0.05em;
    }
    .ai-badge::before {
        content: '🤖';
        font-size: 1rem;
    }
    .subtitle {
        color: var(--text-muted);
        font-size: 0.875rem;
        margin-top: 0.75rem;
    }
    .stats {
        display: flex;
        justify-content: center;
        gap: 3rem;
        margin: 3rem 0;
        padding: 2rem;
        background: var(--bg-card);
        border-radius: 12px;
        border: 1px solid var(--border);
    }
    .stat { text-align: center; }
    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--accent-gold);
    }
    .stat-label {
        color: var(--text-muted);
        font-size: 0.875rem;
        margin-top: 0.5rem;
    }
    .games-section h2 {
        font-size: 1.25rem;
        color: var(--accent-gold);
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--accent-gold);
        display: inline-block;
    }
    .game-list { display: flex; flex-direction: column; gap: 1rem; }

    /* 卡片 */
    .game-card {
        background: var(--bg-card);
        border-radius: 10px;
        padding: 1rem 1.25rem;
        border: 1px solid var(--border);
        display: grid;
        grid-template-columns: auto 1fr auto;
        align-items: center;
        gap: 1.25rem;
        transition: all 0.3s ease;
    }
    .game-card:hover {
        border-color: var(--accent-gold);
        transform: translateX(8px);
        box-shadow: 0 0 20px rgba(230, 184, 0, 0.2);
    }

    /* 结果圆圈 */
    .game-result {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        font-weight: 700;
        flex-shrink: 0;
    }
    .result-win { background: linear-gradient(135deg, #22c55e, #16a34a); color: white; }
    .result-draw { background: linear-gradient(135deg, #f59e0b, #d97706); color: white; }
    .result-loss { background: linear-gradient(135deg, #ef4444, #dc2626); color: white; }

    /* 信息区域 */
    .game-info h3 {
        font-size: 1rem;
        margin-bottom: 0.35rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    .game-date {
        font-size: 0.75rem;
        color: var(--text-muted);
        font-weight: 400;
    }
    .game-meta {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        color: var(--text-muted);
        font-size: 0.8rem;
        flex-wrap: wrap;
    }
    .game-color {
        padding: 0.15rem 0.4rem;
        border-radius: 4px;
        font-size: 0.65rem;
        font-weight: 500;
    }
    .color-white { background: #f8fafc; color: #1e293b; }
    .color-black { background: #334155; color: #f1f5f9; }
    .meta-dot { color: var(--border); }

    /* 指标标签 */
    .metric-tag {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        font-size: 0.72rem;
        line-height: 1.4;
        font-weight: 500;
    }
    .metric-tag.green {
        background: rgba(74, 222, 128, 0.15);
        border: 1px solid rgba(74, 222, 128, 0.4);
        color: var(--accent-green);
    }
    .metric-tag.green .value { font-weight: 700; }
    .metric-tag.red {
        background: rgba(248, 113, 113, 0.15);
        border: 1px solid rgba(248, 113, 113, 0.4);
        color: var(--accent-red);
    }
    .metric-tag.red .value { font-weight: 700; }

    /* 步数和分钟标签 */
    .metric-basic {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        font-size: 0.72rem;
        line-height: 1.4;
        background: rgba(230, 184, 0, 0.1);
        border: 1px solid rgba(230, 184, 0, 0.3);
        color: var(--accent-gold);
    }
    .metric-basic .value { font-weight: 600; }

    /* 分析时间标签 */
    .metric-time {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        font-size: 0.72rem;
        line-height: 1.4;
        background: rgba(139, 92, 246, 0.15);
        border: 1px solid rgba(139, 92, 246, 0.4);
        color: #a78bfa;
    }
    .metric-time .value { font-weight: 600; }

    /* 链接 */
    .game-link {
        color: var(--accent-gold);
        text-decoration: none;
        padding: 0.4rem 0.85rem;
        border: 1px solid var(--accent-gold);
        border-radius: 6px;
        transition: all 0.3s ease;
        font-size: 0.8rem;
        font-weight: 500;
        flex-shrink: 0;
    }
    .game-link:hover {
        background: var(--accent-gold);
        color: var(--bg-dark);
    }
    footer {
        text-align: center;
        margin-top: 4rem;
        padding-top: 2rem;
        border-top: 1px solid var(--border);
        color: var(--text-muted);
        font-size: 0.875rem;
    }
    @media (max-width: 768px) {
        .container { padding: 1.5rem 1rem; }
        .brand-name { font-size: 2.5rem; }
        .slogan { font-size: 1rem; }
        .stats { gap: 1rem; padding: 1rem; }
        .stat-value { font-size: 1.75rem; }
        .game-card {
            grid-template-columns: auto 1fr;
            gap: 1rem;
            padding: 1rem;
        }
        .game-link { grid-column: 1 / -1; text-align: center; }
        .game-meta { flex-wrap: wrap; }
    }
"""

GAME_CSS = """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    :root {
        --bg-dark: #1a1a2e;
        --bg-card: #16213e;
        --accent-gold: #e6b800;
        --text-light: #f1f5f9;
        --text-muted: #94a3b8;
        --border: #334155;
    }
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background: var(--bg-dark);
        color: var(--text-light);
        min-height: 100vh;
        padding: 2rem;
    }
    .container {
        max-width: 800px;
        margin: 0 auto;
    }
    .back-link {
        display: inline-block;
        margin-bottom: 2rem;
        color: var(--accent-gold);
        text-decoration: none;
        font-size: 0.875rem;
    }
    .back-link:hover { text-decoration: underline; }
    .content {
        background: var(--bg-card);
        border-radius: 12px;
        padding: 2.5rem;
        border: 1px solid var(--border);
    }
    h1 {
        font-size: 1.75rem;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid var(--border);
    }
    .content h2 {
        color: var(--accent-gold);
        font-size: 1.1rem;
        margin: 1.5rem 0 0.75rem;
    }
    .content h3 {
        color: var(--text-light);
        font-size: 1rem;
        margin: 1rem 0 0.5rem;
    }
    .content p { line-height: 1.8; margin-bottom: 1rem; }
    .content ul, .content ol { margin-left: 1.5rem; margin-bottom: 1rem; }
    .content li { line-height: 1.8; margin-bottom: 0.25rem; }
    .content strong { color: var(--accent-gold); }
    .content code {
        background: var(--bg-dark);
        padding: 0.2rem 0.4rem;
        border-radius: 3px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9em;
    }
    .content pre {
        background: var(--bg-dark);
        padding: 1rem;
        border-radius: 8px;
        overflow-x: auto;
        margin: 1rem 0;
    }
    .content pre code { background: none; padding: 0; }
    .content hr {
        border: none;
        border-top: 1px solid var(--border);
        margin: 1.5rem 0;
    }
    .board-image {
        display: block;
        max-width: 100%;
        border-radius: 8px;
        margin: 0 auto 2rem;
        border: 2px solid var(--accent-gold);
        box-shadow: 0 0 20px rgba(230, 184, 0, 0.3);
    }
    .board-image-caption {
        text-align: center;
        color: var(--text-muted);
        font-size: 0.8rem;
        margin-top: -1.5rem;
        margin-bottom: 2rem;
    }
    @media (max-width: 768px) {
        body { padding: 1rem; }
        .container { padding: 0; }
        .content { padding: 1.5rem; }
        h1 { font-size: 1.25rem; }
        .content h2 { font-size: 1rem; }
    }
"""

def generate_index_html():
    """Generate index.html with Style A (dark chess theme)."""
    games = get_game_list()

    # Calculate stats
    total = len(games)
    wins = sum(1 for g in games if g['result'] == '胜')
    draws = sum(1 for g in games if g['result'] == '和')
    losses = sum(1 for g in games if g['result'] == '败')

    games_html = ''
    result_class_map = {'胜': 'win', '和': 'draw', '败': 'loss'}
    for g in games:
        link = f"./{g['filename'].replace('.md', '.html')}"
        color_class = 'color-white' if g['color'] == '执白' else 'color-black'
        result_class = f'result-{result_class_map.get(g["result"], g["result"])}'
        games_html += f"""
        <div class="game-card">
            <div class="game-result {result_class}">{g['result']}</div>
            <div class="game-info">
                <h3>vs {g['opponent']} <span class="game-date">· {g['date']}</span></h3>
                <div class="game-meta">
                    <span class="game-color {color_class}">{g['color']}</span>
                    <span class="meta-dot">·</span>
                    <span class="metric-basic">♟ <span class="value">{g['steps']}</span> 步</span>
                    <span class="meta-dot">·</span>
                    <span class="metric-basic">⏱ <span class="value">{g['time_control']}</span></span>
                    <span class="meta-dot">·</span>
                    <span class="metric-tag green">✨ <span class="value">{g['highlights']}</span> 亮点</span>
                    <span class="metric-tag red">⚠️ <span class="value">{g['mistakes']}</span> 失误</span>
                    <span class="meta-dot">·</span>
                    <span class="metric-time">📝 <span class="value">{g['analyze_time']}</span></span>
                </div>
            </div>
            <a href="{link}" class="game-link">查看 →</a>
        </div>
"""

    template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChessLens - AI Chess Review</title>
    <style>{INDEX_CSS}</style>
</head>
<body>
    <div class="container">
        <header>
            <div class="brand-name">ChessLens</div>
            <div class="slogan">Review Smarter, Improve Faster</div>
            <div class="ai-badge">🤖 AI-Powered Chess Review</div>
            <p class="subtitle">aaronwang2026 的对局记录</p>
        </header>

        <div class="stats">
            <div class="stat">
                <div class="stat-value">{total}</div>
                <div class="stat-label">总对局</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: #22c55e;">{wins}</div>
                <div class="stat-label">胜</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: #f59e0b;">{draws}</div>
                <div class="stat-label">和</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: #ef4444;">{losses}</div>
                <div class="stat-label">败</div>
            </div>
        </div>

        <section class="games-section">
            <h2>近期对局</h2>
            <div class="game-list">
                {games_html}
            </div>
        </section>

        <footer>
            <p>♔ ChessLens · Review Smarter, Improve Faster</p>
        </footer>
    </div>
</body>
</html>"""
    return template

def generate_game_html(filename):
    """Generate HTML for a single game markdown file."""
    md_content = read_file(os.path.join(SRC_DIR, filename))

    # Extract chess.com link if exists (line like 🔗 [Chess.com 对局链接](https://...))
    import re
    chess_com_link = ''
    link_pattern = r'🔗 \[Chess\.com[^\]]*\]\((https?://[^\)]+)\)'
    match = re.search(link_pattern, md_content)
    if match:
        url = match.group(1)
        chess_com_link = f'<p>🔗 <a href="{url}" target="_blank" rel="noopener">查看 Chess.com 详情</a></p>'
        # Remove the link line from content
        md_content = re.sub(link_pattern, '', md_content, count=1)

    # Find 总体评价 and insert link after it
    body_html = mistune.html(md_content)
    if chess_com_link:
        body_html = re.sub(
            r'(<p><strong>总体评价：</strong>.*?</p>)',
            r'\1\n            ' + chess_com_link,
            body_html,
            flags=re.DOTALL
        )

    title = filename.replace('.md', '').replace('_', ' ')

    # Insert board image if it exists (same game_id)
    import re as re2
    game_id_match = re2.search(r'^(\d{4}-\d{2}-\d{2})_([^_]+)_', filename)
    board_image_html = ''
    if game_id_match:
        game_id = game_id_match.group(2)
        images_dir = os.path.join(os.path.dirname(SRC_DIR), 'images')
        # Look for image with matching game_id
        if os.path.exists(images_dir):
            for img_file in os.listdir(images_dir):
                if game_id in img_file and img_file.endswith('.png'):
                    img_url = f"reviews/images/{img_file}"
                    board_image_html = f'''
            <img src="{img_url}" alt="棋局终局局面" class="board-image">
            <p class="board-image-caption">终局局面（点击查看 Chess.com 完整复盘）</p>
'''
                    break

    # Get analyze time from file modification time
    file_path = os.path.join(SRC_DIR, filename)
    analyze_time = get_file_mtime(file_path)

    template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>{GAME_CSS}</style>
</head>
<body>
    <div class="container">
        <a href="./index.html" class="back-link">← 返回列表</a>
        <p style="color: var(--text-muted); font-size: 0.875rem; margin-bottom: 1rem;">📝 分析时间：{analyze_time}</p>
        {board_image_html}
        <div class="content">
            {body_html}
        </div>
    </div>
</body>
</html>"""
    return template

def main():
    """Main build function."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    index_html = generate_index_html()
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)

    for f in get_md_files():
        html = generate_game_html(f)
        output_path = os.path.join(OUTPUT_DIR, f.replace('.md', '.html'))
        with open(output_path, 'w', encoding='utf-8') as out:
            out.write(html)

    print(f"Generated site with {len(get_md_files()) + 1} pages in {OUTPUT_DIR}/")

if __name__ == '__main__':
    main()
