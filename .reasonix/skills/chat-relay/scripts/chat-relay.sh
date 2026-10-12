#!/usr/bin/env bash
# chat-relay：chat 接力模式开关
# 用法：chat-relay.sh {on|off|status|check}
#   on/off/status  开关写入与报告（agent／用户调用）
#   check          UserPromptSubmit 钩子：开启时注入模式提醒，关闭时静默；永远退出 0
set -u

# 仓库根解析：显式覆盖 CHAT_RELAY_ROOT > CLAUDE_PROJECT_DIR > 脚本位置上溯四级
if [ -n "${CHAT_RELAY_ROOT:-}" ]; then
  ROOT="$CHAT_RELAY_ROOT"
elif [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
  ROOT="$CLAUDE_PROJECT_DIR"
else
  ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." 2>/dev/null && pwd)" || ROOT=""
fi

SWITCH_DIR="$ROOT/chat-relay"        # 仓库根：仅开关
SWITCH="$SWITCH_DIR/ON"
cmd="${1:-status}"

case "$cmd" in
  check)
    [ -n "$ROOT" ] && [ -f "$SWITCH" ] || exit 0
    printf '%s\n' "[chat-relay 模式开启中] 内容走 chat，运行走执行：① 需人理解/讨论/判断/成稿的内容，与需独立判定者的锚定判读（DA-1 类）——先分析备料（对应选题下 chat-relay/{会话}/：提示词.md + 上传包/），交用户带去 ChatGPT，带回后必须表态（保真/事实/可装回），同意才按归属 skill 契约实施；② 判读/编码/计算等生产数据的执行性运行——不路由 chat，由执行侧启动对应 skill（research-executor 等）。做备料／回程／表态前先读 .reasonix/skills/chat-relay/references/protocol.md。关闭：/chat-relay off"
    exit 0
    ;;
esac

if [ -z "$ROOT" ]; then
  echo "chat-relay：无法定位仓库根（可设 CHAT_RELAY_ROOT）" >&2
  exit 2
fi

case "$cmd" in
  on)
    mkdir -p "$SWITCH_DIR"
    if [ -f "$SWITCH" ]; then
      echo "chat-relay：已是开启状态"
    else
      touch "$SWITCH"
      echo "chat-relay：已开启。之后需要人理解/讨论/判断/成稿的内容会先备料（提示词＋上传包）交你带去 ChatGPT，带回后表态、同意才实施；判读/编码等执行性运行由执行侧 skill 直接做，不经 chat。关闭：/chat-relay off"
    fi
    ;;
  off)
    if [ -f "$SWITCH" ]; then
      rm -f "$SWITCH"
      echo "chat-relay：已关闭（在途会话保留在各选题的 chat-relay/ 目录）"
    else
      echo "chat-relay：本来就是关闭状态"
    fi
    ;;
  status)
    if [ -f "$SWITCH" ]; then echo "开关：开启中"; else echo "开关：关闭"; fi
    found=0
    # 会话归各选题：topics/**/chat-relay/*/台账.md（find 不写死层级，平铺与分组布局通用）
    while IFS= read -r ledger; do
      [ -f "$ledger" ] || continue
      d="$(dirname "$ledger")"
      topic="$(basename "$(dirname "$(dirname "$d")")")"
      if [ "$found" -eq 0 ]; then echo "在途会话："; found=1; fi
      state="$(grep -m1 -e '^- 状态：' "$ledger" 2>/dev/null | sed 's/^- 状态：//' || true)"
      printf '  - %s/%s：%s\n' "$topic" "$(basename "$d")" "${state:-（无状态行）}"
    done < <(find "$ROOT/topics" -type f -name '台账.md' -path '*/chat-relay/*' 2>/dev/null | LC_ALL=C sort)
    [ "$found" -eq 1 ] || echo "在途会话：无"
    ;;
  *)
    echo "用法：chat-relay.sh {on|off|status|check}" >&2
    exit 2
    ;;
esac
