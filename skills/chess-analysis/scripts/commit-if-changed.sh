#!/bin/bash
# commit-if-changed.sh — 检测 analyses 目录变更，立即 commit + push

set -e

REVIEWS_DIR="$HOME/chessLens/chess-reviews-summary/docs"
GIT_DIR="$HOME/chessLens/chess-reviews-summary"
AUTHOR_NAME="aaronwang2026 Analyst"
AUTHOR_EMAIL="5109343@qq.com"

cd "$GIT_DIR"
git config user.name "$AUTHOR_NAME" 2>/dev/null || true
git config user.email "$AUTHOR_EMAIL" 2>/dev/null || true

# 同步最新文件到 docs/ 目录
mkdir -p "$GIT_DIR/docs"
cp -f "$REVIEWS_DIR"/*.md "$GIT_DIR/docs/" 2>/dev/null || true

# 检查是否有变更
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard 2>/dev/null)" ]; then
    echo "No changes detected"
    exit 0
fi

# Commit + Push（立即同步）
validate_review_format() {
    local file="$1"
    local errors=0

    # 必须包含的正确标题
    if ! grep -qE '^## 🎯 亮点时刻' "$file"; then
        echo "❌ $file: 缺少 '## 🎯 亮点时刻' 标题（不是 ## 💥 昏着）"
        errors=$((errors + 1))
    fi

    if ! grep -qE '^## ⚠️ 关键失误（按重要性排序）' "$file"; then
        echo "❌ $file: 缺少 '## ⚠️ 关键失误（按重要性排序）' 标题"
        errors=$((errors + 1))
    fi

    # 亮点必须是 "- **第X步" 格式，不允许 "### 🚨" 或 "1. **"
    if grep -qE '^### 🚨' "$file"; then
        echo "❌ $file: 包含 ### 🚨 子标题（禁止使用，必须用 - **第X步 格式）"
        errors=$((errors + 1))
    fi

    # 失误必须是 "1. **第X步" 格式
    if ! grep -qE '^1\. \*\*第' "$file"; then
        echo "❌ $file: 缺少 '1. **第X步' 格式的失误条目"
        errors=$((errors + 1))
    fi

    return $errors
}

echo "Validating format of new/changed md files..."
for f in docs/*.md; do
    if [ -f "$f" ]; then
        if ! validate_review_format "$f"; then
            echo ""
            echo "格式验证失败，请修正后再提交！"
            exit 1
        fi
    fi
done
echo "格式验证通过 ✓"
echo ""

# Commit + Push（立即同步）
git add -A
git commit -m "Auto-commit: chess reviews $(date '+%Y-%m-%d %H:%M')"
git push origin main

echo "Push done, waiting for GitHub Pages deployment..."

# 验证 GitHub Pages 是否已更新
# 策略：从最近新增的 md 文件提取对手名，检测页面是否包含该记录
SITE_URL="https://wldandan.github.io/chess-reviews-summary/"
MAX_WAIT=120
INTERVAL=10
elapsed=0

# 取最新文件的文件名（不含扩展名），提取对手名用于验证
latest_file=$(ls -t "$REVIEWS_DIR"/*.md 2>/dev/null | head -1)
if [ -z "$latest_file" ]; then
    echo "No review file found, skipping verification"
    exit 0
fi

# 从文件名提取对手名（格式：日期_执白_胜负_执白vs{对手名}_...）
# 例如: 2026-04-20_167564728910_aaronwang2026_执黑负_zDrix_27步_1800.html
opponent=$(basename "$latest_file" .md | sed -E 's/.*[负胜]_(.+)_[0-9]+步.*/\1/')
echo "Verifying opponent: $opponent"

# 从本地 md 提取关键字段（兼容新旧两种格式）
# 步数：新格式"共 N 步" 或 旧格式表格"| 步数 | N 步|"
steps_local=$(grep "共 " "$latest_file" | sed -E 's/.*共 ([0-9]+) 步.*/\1/' | head -1)
if [ -z "$steps_local" ]; then
    steps_local=$(grep "步数" "$latest_file" | grep -oE '[0-9]+' | head -1)
fi

# 亮点：新格式正文"🎯 "开头行 或 旧格式表格标注
highlights_local=$(grep -c "^🎯 " "$latest_file" 2>/dev/null || echo "0")
if [ "$highlights_local" = "0" ]; then
    # 旧格式：统计"✨"标注行数
    highlights_local=$(grep -c "✨" "$latest_file" 2>/dev/null || echo "0")
fi

# 失误：新格式"💥 BLUNDER"行 或 旧格式表格"💥"标注
blunders_local=$(grep -c "💥 BLUNDER" "$latest_file" 2>/dev/null || echo "0")
if [ "$blunders_local" = "0" ]; then
    blunders_local=$(grep "💥" "$latest_file" | grep -c "BLUNDER\|失误" 2>/dev/null || echo "0")
fi

echo "Local: 亮点=$highlights_local 失误=$blunders_local 步数=$steps_local"

while [ $elapsed -lt $MAX_WAIT ]; do
    # 抓取页面，找到对手所在卡片的完整 HTML
    page_html=$(curl -sf --max-time 10 "$SITE_URL" 2>/dev/null)
    if echo "$page_html" | grep -q "$opponent"; then
        # 提取该对手卡片区块（从对手名到"查看"链接之间）
        card_html=$(echo "$page_html" | grep -B20 "$opponent" | grep -A20 "game-link" | head -25)

        # 从卡片提取亮点/失误数（macOS grep 无 -P，用 grep -oE 配合 grep 先定位行）
        highlights_web=$(echo "$card_html" | grep '✨' | grep -oE '[0-9]+' | head -1)
        blunders_web=$(echo "$card_html" | grep '⚠️' | grep -oE '[0-9]+' | head -1)
        steps_web=$(echo "$card_html" | grep '♟' | grep -oE '[0-9]+' | head -1)

        echo "Web:   亮点=$highlights_web 失误=$blunders_web 步数=$steps_web"

        # 对比关键字段
        all_ok=true
        if [ "$highlights_local" != "$highlights_web" ]; then
            echo "  ⚠️ 亮点不匹配: 本地=$highlights_local 网页=$highlights_web"
            all_ok=false
        fi
        if [ "$blunders_local" != "$blunders_web" ]; then
            echo "  ⚠️ 失误不匹配: 本地=$blunders_local 网页=$blunders_web"
            all_ok=false
        fi
        if [ "$steps_local" != "$steps_web" ]; then
            echo "  ⚠️ 步数不匹配: 本地=$steps_local 网页=$steps_web"
            all_ok=false
        fi

        if $all_ok; then
            echo "✓ Verified: '$opponent' found on $SITE_URL with matching fields"
            echo "Done: committed, pushed, and verified"
            exit 0
        else
            echo "✓ Opponent found but fields mismatch — manual review needed"
            echo "Done: committed and pushed, verification failed"
            exit 0
        fi
    fi
    elapsed=$((elapsed + INTERVAL))
    echo "  Waiting... ${elapsed}s/${MAX_WAIT}s"
    sleep $INTERVAL
done

echo "⚠️ Warning: '$opponent' not found on $SITE_URL after ${MAX_WAIT}s — manual check needed"
echo "Done: committed and pushed, but verification timed out"
