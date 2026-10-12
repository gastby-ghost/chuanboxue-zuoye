# 项目指导（AGENTS.md）

## chat-relay 模式：每轮先查开关

本仓库装有 chat-relay skill（`.reasonix/skills/chat-relay/`，内容走 chat、运行走执行）。原 Claude Code 版的每轮提醒由 UserPromptSubmit 钩子注入，本仓库改用本文件登记。

**每轮收到用户消息后、开始工作前，先运行一次**：

```bash
bash .reasonix/skills/chat-relay/scripts/chat-relay.sh check
```

- 有输出 → 该行即本轮模式提醒，按它行事；做备料／回程／表态前读 `.reasonix/skills/chat-relay/references/protocol.md`。
- 无输出 → 模式关闭，静默继续。

**开关只由用户命令触发**（`/chat-relay`、`/chat-relay off`、`/chat-relay status`）：执行 `chat-relay.sh {on|off|status}` 并把输出直接报给用户；不自动开启。开关行为与进入／恢复规则见 `.reasonix/skills/chat-relay/SKILL.md`。
