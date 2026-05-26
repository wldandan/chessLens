#!/bin/bash
set -e

# Git Sync Script for Chess Reviews
# Syncs review results to the chess-reviews-summary repository

REVIEWS_REPO="git@github.com:wldandan/chess-reviews-summary.git"
REVIEWS_DIR="$HOME/chessLens/chess-reviews-summary"

# Function to sync reviews
sync_reviews() {
    local message="${1:-Update chess review}"

    # Clone or pull the reviews repo
    if [ -d "$REVIEWS_DIR/.git" ]; then
        cd "$REVIEWS_DIR"
        git pull --rebase origin main
    else
        git clone "$REVIEWS_REPO" "$REVIEWS_DIR"
        cd "$REVIEWS_DIR"
    fi

    # Copy new review files from workspace memory
    local workspace_memory="$HOME/.openclaw/workspace-chess-ai-coach/memory"
    if [ -d "$workspace_memory" ] && [ "$(ls -A "$workspace_memory" 2>/dev/null)" ]; then
        # Copy new/changed memory files
        for f in "$workspace_memory"/*.md; do
            if [ -f "$f" ]; then
                cp "$f" .
                git add "$(basename "$f")"
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
