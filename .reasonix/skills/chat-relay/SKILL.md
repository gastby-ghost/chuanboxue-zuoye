---
name: chat-relay
description: "chat 接力模式开关：开启后附加于全部 skill 之上——需要人理解与判断的内容（讨论/成稿/锚定判读）以 ChatGPT 为主场：agent 备料（提示词＋上传包）、用户带去讨论、带回后 agent 表态、同意即按归属契约实施；判读/编码等执行性运行不走此通道，归执行侧 skill。"
---

# chat-relay — chat 接力模式

> 内容生产线上的一道「人话关」：凡需要人理解、讨论、判断、成稿的**内容**（含需独立判定者的锚定判读），改由 chat（ChatGPT）与用户讨论产出；agent 只做备料、表态与实施。
>
> **分流边界（2026-10-12 用户裁定）：内容走 chat，运行走执行。** 判读／编码／计算等**生产数据的执行性运行**（可复算、可复跑、可对照）不走本通道——由执行侧启动对应 skill（research-executor 等）完成。
>
> **本文件只管开关与入口。** 备料、回程、表态、收敛的完整工作规程在 `references/protocol.md`——做接力前先读它；chat 分享链接回程的格式说明在 `references/chatgpt-share-format.md`。

## 开关

执行即 `bash .reasonix/skills/chat-relay/scripts/chat-relay.sh {on|off|status}`，把脚本输出直接报给用户。

| 命令 | 动作 |
|---|---|
| `/chat-relay` | 开启；已开启则报「已是开启状态」 |
| `/chat-relay off` | 关闭（在途会话文件保留） |
| `/chat-relay status` | 只读报告：开关＋在途会话及各自等谁 |

- 开关只由用户斜杠命令触发，不自动开启。
- 开关文件：`chat-relay/ON`（仓库根，gitignore）；会话目录：`topics/<选题>/chat-relay/{会话}/`（同样不入库）。
- 持续机制：每轮注入一行模式提醒，原由 Claude Code 的 UserPromptSubmit 钩子承担；本仓库已登记在项目 `AGENTS.md`——每轮先执行 `bash .reasonix/skills/chat-relay/scripts/chat-relay.sh check`，有输出即按提醒行事，不依赖记忆。

## 进入与进度识别

2026-10-10 用户裁决：开新会话就是新会话——进入不预扫，按下表动作。

| 情形 | 动作 |
|---|---|
| 裸 `/chat-relay` 或 `off` | 只读写开关、报脚本输出；**不扫在途会话、不读台账** |
| `/chat-relay status` | 显式查询才扫描；只读报告，不推进工作 |
| 用户说「继续」或带回产出 | 到那时才定位会话：「继续」接最近一个未收敛的；带回按用户指到的话题。**不预先全库扫** |

定位到会话之后的工作（落盘、表态、实施）按 `references/protocol.md` 执行。
