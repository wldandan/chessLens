#!/bin/bash
# Verify a ChessLens review actually builds locally and (optionally) goes live on GitHub Pages.
#
# Usage:
#   scripts/verify_publish.sh <game_id>            # 本地层：源就位 + 构建 + 断言新页/首页
#   scripts/verify_publish.sh <game_id> --remote   # 再加线上层：gh run watch + 线上 200/收录
#
# 退出码非 0 = 验证失败（任何一步红就停）。
set -euo pipefail

GAME_ID="${1:-}"
REMOTE=0
[[ "${2:-}" == "--remote" ]] && REMOTE=1
if [[ -z "$GAME_ID" ]]; then
  echo "用法: scripts/verify_publish.sh <game_id> [--remote]" >&2
  exit 2
fi

PAGES_BASE="https://wldandan.github.io/chessLens"
SRC_DIR="docs/reviews/docs"
OUT_DIR="docs"
green() { printf '\033[32m✅ %s\033[0m\n' "$1"; }
red()   { printf '\033[31m❌ %s\033[0m\n' "$1"; }

echo "── 第1层：本地构建验证 ──"

# 0. 源就位检查（防 generate.py 把首页清空再 push）
src_count=$(find "$SRC_DIR" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ' || true)
if [[ "$src_count" -eq 0 ]]; then
  red "$SRC_DIR 为空 — 复盘 md 源未就位（应已 commit 在仓库内）。终止，避免清空首页。"
  exit 1
fi
green "源就位：$SRC_DIR 有 $src_count 个 md"
if ! ls "$SRC_DIR"/*_"${GAME_ID}"_*.md >/dev/null 2>&1; then
  red "源里找不到 game_id=$GAME_ID 的复盘 md（先跑 analyze.py 并同步到 $SRC_DIR）"
  exit 1
fi
green "源含本局 md"

# 1. 构建
python3 .github/workflows/generate.py

# 2. 断言新页 + 首页收录
page=$(ls "$OUT_DIR"/*_"${GAME_ID}"_*.html 2>/dev/null | head -1 || true)
if [[ -z "$page" ]]; then
  red "构建后未生成 $OUT_DIR/*_${GAME_ID}_*.html"
  exit 1
fi
green "已生成对局页：$page"
if grep -q "$GAME_ID" "$OUT_DIR/index.html"; then
  green "首页已收录本局"
else
  red "index.html 未收录 game_id=$GAME_ID"
  exit 1
fi

if [[ "$REMOTE" -eq 0 ]]; then
  echo; green "本地验证通过。push 后加 --remote 验证线上。"
  exit 0
fi

echo; echo "── 第2层：线上发布验证 ──"

# 3. 等最近一次 deploy.yml 跑完
run_id=$(gh run list -w deploy.yml -L1 --json databaseId -q '.[0].databaseId')
echo "watching deploy run $run_id ..."
if ! gh run watch "$run_id" --exit-status; then
  red "GitHub Actions deploy 失败 (run $run_id)"
  exit 1
fi
green "Actions deploy 成功"

# 4. 线上单页可达 + 首页收录（URL 编码中文文件名；CDN 滞后则重试）
fname=$(basename "$page")
url=$(python3 -c "import urllib.parse,sys; print('$PAGES_BASE/'+urllib.parse.quote(sys.argv[1]))" "$fname")
code=000
for i in 1 2 3 4 5; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)
  [[ "$code" == "200" ]] && break
  echo "  线上页暂 $code，CDN 滞后，30s 后重试 ($i/5)…"; sleep 30
done
if [[ "$code" == "200" ]]; then green "线上对局页 200：$url"; else red "线上对局页不可达 (HTTP $code)：$url"; exit 1; fi

if curl -s "$PAGES_BASE/" | grep -q "$GAME_ID"; then
  green "线上首页已收录本局"
else
  red "线上首页未收录 game_id=$GAME_ID（可能 CDN 未刷新，稍后重试）"
  exit 1
fi

echo; green "发布验证全绿 🎉  $url"
