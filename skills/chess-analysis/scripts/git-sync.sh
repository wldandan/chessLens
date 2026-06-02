#!/bin/bash
set -e

# Git Sync Script for Chess Reviews
# Syncs review results into the consolidated chessLens repository (single-repo).
# 每盘一个目录 games/{date}_{opp}_{id}/，CI(deploy.yml) 负责构建 html。

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"   # chessLens repo root
GAMES_DIR="$REPO_DIR/games"
USER="${CURRENT_CHESS_USER:-aaronwang2026}"

# 从复盘 md 文件名推导目录 games/{date}_{对手}_{id}
game_dir_for() {
    local base; base="$(basename "$1" .md)"
    local IFS='_'; read -ra p <<< "$base"
    local date="${p[0]}" gid="${p[1]}" opp="${p[2]}"
    [ "$opp" = "$USER" ] && opp="${p[4]}"
    echo "$GAMES_DIR/${date}_${opp}_${gid}"
}

# Function to sync reviews
sync_reviews() {
    local message="${1:-Update chess review}"

    cd "$REPO_DIR"
    git pull --rebase origin main || true

    # Copy new review files from workspace memory, each into its own game dir
    local workspace_memory="$HOME/.openclaw/workspace-chess-ai-coach/memory"
    if [ -d "$workspace_memory" ] && [ "$(ls -A "$workspace_memory" 2>/dev/null)" ]; then
        for f in "$workspace_memory"/*.md; do
            if [ -f "$f" ]; then
                local d; d="$(game_dir_for "$f")"
                mkdir -p "$d"
                cp "$f" "$d/"
                git add "${d#$REPO_DIR/}/$(basename "$f")"
            fi
        done
    fi

    # Commit and push if there are changes
    if git diff --cached --quiet; then
        echo "No changes to sync"
        return 0
    fi

    git commit -m "$message"
    git push origin main
    echo "Reviews synced successfully"
}

# Run if called directly
if [ "$(basename "$0")" = "git-sync.sh" ]; then
    sync_reviews "$@"
fi
