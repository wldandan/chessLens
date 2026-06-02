# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ChessLens is Aaron Wang's (aaronwang2026) chess improvement system. It captures games from chess.com, performs AI-powered review using Stockfish, generates static HTML reports, and publishes them to GitHub Pages.

**Data path** (single-repo): review markdown + images live in-repo at `docs/reviews/docs/` and `docs/reviews/images/`. CI (`deploy.yml`) builds `docs/*.html` from them. The former separate `chess-reviews-summary` repo has been merged in and retired.

---

## Build & Test

### Generate static site (GitHub Pages)
```bash
python3 .github/workflows/generate.py
```
Output: `docs/index.html` + `docs/*.html`

### CI/CD
- GitHub Actions deploys on push to `main` via `.github/workflows/deploy.yml`
- Builds Python 3.12, installs `mistune`, runs `generate.py`, uploads `docs/` to GitHub Pages

### Stockfish analysis
```bash
python3 skills/chess-analysis/scripts/analyze.py --pgn-file game.pgn 16
python3 skills/chess-analysis/scripts/analyze.py "PGN..." 20 --focus-user aaronwang2026
```
- Auto-detects Stockfish at `/opt/homebrew/bin/stockfish`, `/opt/homebrew/bin/stockfish-mac`, or `PATH`
- Default depth: 16

### Sync and commit review docs
```bash
bash skills/chess-analysis/scripts/git-sync.sh
bash skills/chess-analysis/scripts/commit-if-changed.sh
```

---

## Architecture

```
chess.com API / agent-browser
         ↓
   PGN extraction
         ↓
   analyze.py (Stockfish)
         ↓
   Markdown review docs/
         ↓
   generate.py (mistune)
         ↓
   docs/index.html + docs/*.html → GitHub Pages
```

### Directory structure
- `skills/chess-analysis/` — chess-analysis skill with `analyze.py`
- `skills/chess-game-history/` — game fetcher skill (chess.com API + agent-browser)
- `skills/chess-player-stats/` — player stats skill (chess.com API)
- `scripts/` — `make_video.py`, `make_cards.py`, `render_board.py`, `parse_review.py`, `generate_blunder_images.py`
- `docs/reviews/docs/` — individual game review markdown files
- `docs/reviews/images/` — chess.com board screenshots
- `docs/reviews/videos/` — generated video files
- `templates/ANALYSIS_TEMPLATE.md` — review doc template

### Review doc filename format
```
{日期}_{game_id}_{白方}_{执白结果}_{黑方}_{回合数}步_{time_control}.md
```
Example: `2026-05-24_169159534058_aaronwang2026_执白胜_itsbishara_41步_600.md`

### Key skills
- `CURRENT_CHESS_USER` env var defaults to `aaronwang2026` if not set
- chess.com API is public (no API key), rate limit ~1 req/sec
- **Game history is newest-last** — API returns oldest first, use `max(games, key=...)` to get latest

---

## Graphify Knowledge Graph

This project has a graphify knowledge graph at `graphify-out/`. Before answering architecture or codebase questions, read `graphify-out/GRAPH_REPORT.md` for god nodes and community structure. If `graphify-out/wiki/index.md` exists, navigate it instead of reading raw files. After modifying code files, run `graphify update .` to keep the graph current.