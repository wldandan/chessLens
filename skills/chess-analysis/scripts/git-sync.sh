#!/bin/bash
set -e

# Git Sync Script for Chess Reviews
# Syncs review results into the consolidated chessLens repository (single-repo).
# 复盘 md 落在 docs/reviews/docs/，CI(deploy.yml) 负责构建 html。

REVIEWS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"   # chessLens repo root
DOCS_DIR="$REVIEWS_DIR/docs/reviews/docs"

# Function to sync reviews
sync_reviews() {
    local message="${1:-Update chess review}"

    cd "$REVIEWS_DIR"
    git pull --rebase origin main || true
    mkdir -p "$DOCS_DIR"

    # Copy new review files from workspace memory
    local workspace_memory="$HOME/.openclaw/workspace-chess-ai-coach/memory"
    if [ -d "$workspace_memory" ] && [ "$(ls -A "$workspace_memory" 2>/dev/null)" ]; then
        # Copy new/changed memory files
        for f in "$workspace_memory"/*.md; do
            if [ -f "$f" ]; then
                cp "$f" "$DOCS_DIR/"
                git add "docs/reviews/docs/$(basename "$f")"
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
