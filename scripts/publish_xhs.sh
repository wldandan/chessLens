#!/usr/bin/env bash
# publish_xhs.sh — 半自动把 ChessLens 复盘帖发到小红书(创作服务平台)
#
# 用法:
#   scripts/publish_xhs.sh <post_dir>
#   post_dir 需含: 01_*.png 02_*.png ... (按序号排好) + caption.txt
#   caption.txt 约定: 第1行=标题, 第2行=空行, 第3行起=正文(含话题标签)
#
# 设计原则(铁律):
#   * 永远停在「发布」前,绝不自动点最终发布——发布与否由人确认。
#   * 全程匿名素材(由 chess-xhs-post skill 保证),本脚本不改图。
#
# 踩过的坑 & 对策(重要):
#   1. agent-browser 是独立浏览器实例,**不是**用户日常的 Chrome,需要自己登录一次。
#      用固定 --session-name xhs 持久化登录态,下次免登录。
#   2. 上传文件**别用 @ref**(切 tab / DOM 变动后 ref 立刻失效,报
#      "CDP error (DOM.describeNode): Object id doesn't reference a Node")。
#      直接用 CSS 选择器 `input[type=file]` 上传,稳定。
#   3. 一次 upload 可传多张:upload <selector> f1 f2 f3 ...,顺序即图片顺序。
#   4. 标题/正文输入框的 @ref 会随快照变化,每次操作前重新 snapshot 取 ref。
set -euo pipefail

SESSION="xhs"
PUBLISH_URL="https://creator.xiaohongshu.com/publish/publish?source=official"
POST_DIR="${1:?用法: publish_xhs.sh <post_dir>(含 NN_*.png + caption.txt)}"

ab() { agent-browser --session-name "$SESSION" "$@"; }

# 取第一个名字含 $1 的元素 ref(从文本快照里抓 ref=eNN)
ref_for() { ab snapshot -i 2>/dev/null | grep -F "$1" | grep -oE 'ref=e[0-9]+' | head -1 | cut -d= -f2; }

# ---- 0. 校验素材 ----
mapfile -t IMAGES < <(ls "$POST_DIR"/[0-9]*.png 2>/dev/null | sort)
[ "${#IMAGES[@]}" -gt 0 ] || { echo "✗ $POST_DIR 下没有 NN_*.png 图片"; exit 1; }
CAPTION="$POST_DIR/caption.txt"
[ -f "$CAPTION" ] || { echo "✗ 缺少 $CAPTION"; exit 1; }
TITLE="$(head -1 "$CAPTION")"
BODY="$(tail -n +3 "$CAPTION")"   # 跳过标题行 + 空行
echo "● 待发素材:${#IMAGES[@]} 张图"
printf '   - %s\n' "${IMAGES[@]##*/}"
echo "● 标题:$TITLE"

# ---- 1. 登录态检查 ----
ab open "$PUBLISH_URL" >/dev/null 2>&1 || true
ab wait 2500 >/dev/null 2>&1 || true
CUR_URL="$(ab get url 2>/dev/null || echo '')"
if echo "$CUR_URL" | grep -qiE 'login|sign|customer/login'; then
  echo "▲ 未登录。正在打开有头浏览器,请在弹出窗口里完成登录(手机号验证码 / 扫码),"
  echo "  登录成功后重新运行本脚本即可(登录态已存进 --session-name $SESSION)。"
  AGENT_BROWSER_HEADED=1 ab --headed open "$PUBLISH_URL" || true
  exit 2
fi

# ---- 2. 切到「上传图文」模式 ----
TU_REF="$(ref_for '上传图文' || true)"
[ -n "${TU_REF:-}" ] && ab click "@$TU_REF" >/dev/null 2>&1 || true
ab wait 1500 >/dev/null 2>&1 || true

# ---- 3. 上传图片(关键:用 CSS 选择器,别用 @ref) ----
echo "● 上传图片中..."
ab upload "input[type=file]" "${IMAGES[@]}" || {
  echo "✗ 上传失败。请确认已切到「上传图文」页且存在 input[type=file]。"; exit 3; }
ab wait 3000 >/dev/null 2>&1 || true

# ---- 4. 填标题 + 正文(每次重新取 ref) ----
TITLE_REF="$(ref_for '填写标题' || true)"
if [ -n "${TITLE_REF:-}" ]; then
  ab fill "@$TITLE_REF" "$TITLE" >/dev/null 2>&1 || true
  echo "● 标题已填:$TITLE_REF"
else
  echo "▲ 没抓到标题框 ref,请手动 snapshot 后填(占位符「填写标题会有更多赞哦」)。"
fi

# 正文框:标题之后、第一个无名 textbox(避开 地点/群聊 的嵌套 textbox)
BODY_REF="$(ab snapshot -i 2>/dev/null | awk '
  /填写标题/ {seen=1; next}
  seen && /textbox .*ref=e[0-9]+/ { match($0, /ref=e[0-9]+/); print substr($0, RSTART+4, RLENGTH-4); exit }
')"
if [ -n "${BODY_REF:-}" ]; then
  ab fill "@$BODY_REF" "$BODY" >/dev/null 2>&1 || true
  echo "● 正文已填:$BODY_REF(含话题标签)"
else
  echo "▲ 没抓到正文框 ref,请手动填入 caption.txt 第3行起的内容。"
fi

# ---- 5. 截图留证,停在发布前 ----
SHOT="/tmp/xhs_preview_$(date +%s).png"
ab screenshot "$SHOT" >/dev/null 2>&1 || true
echo
echo "════════════════════════════════════════════════════"
echo " ✅ 已就绪并停在「发布」前。预览截图:$SHOT"
echo " ⛔ 本脚本不会自动点「发布」。请人工核对后手动点击,"
echo "    或运行:agent-browser --session-name $SESSION click @<发布按钮ref>"
echo "════════════════════════════════════════════════════"
