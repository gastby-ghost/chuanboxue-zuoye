# 传播学作业

**AI 能成为舆论"降温器"吗？——AI 搜索对感知极化与意见表达的影响研究（以微博智搜为例）**

## 仓库结构

| 目录 | 内容 |
| --- | --- |
| `docs/` | 研究文档（8 份 .md，见下） |
| `archive/` | 过程档案：两份演进日志；`archive/dialogs/` 存放 AI 对话原始导出（.json） |
| `presentation/` | 小组展示：PPT 内容稿、演讲稿 |
| `figures/` | 图：模型图、理论推导链、实验流程、检验力曲线 |
| `tools/` | 脚本（见「工具」） |
| `.reasonix/skills/` | AI 技能：`chat-relay`（chat 接力模式，见下）、`ai-dialog-export`（生成 `archive/dialogs/` 导出） |

仓库以 `.md` 为**版本化的源文件**；`.docx` 为生成物，不在版本控制中，需要时用 `tools/` 下的脚本按需重新生成。

## 文档一览

### `docs/` —— 研究文档

| 文件 | 说明 |
| --- | --- |
| `研究总览.md` | **全量汇总（入口文档）**：题目、理论、假设、变量、文献、方法、分析、局限一应俱全 |
| `研究设计.md` | **方法与设计的完整版**：研究问题、模型与假设、变量操作化、刺激材料、实验设计、样本与检验力、分析策略、效度局限 |
| `测量工具.md` | **测量与编码**：问卷题项全文、计分表、内容分析编码手册、评论框对立化程度编码手册、伦理与知情同意 |
| `预注册与分析.md` | **预注册与统计**：预注册模板、检验力与敏感性分析、判定规则、零结果预案、SPSS/PROCESS 操作 |
| `理论框架与假设.md` | 主理论（多元无知）、适配性校准、研究模型、假设 H1／H2／H3 |
| `选题.md` | 选题演进与理论资源：一句话概述、因果结构、理论资源、v1→v2 修订说明 |
| `文献框架.md` | 四章文献综述框架、逐章文献落点、术语对照表 |
| `文献综述.md` | 综述正文写作稿：把四章框架逐节展开为可进论文的段落 |

### `archive/` —— 过程档案

| 文件 | 说明 |
| --- | --- |
| `研究从0到1-全过程日志.md` | **过程档案（全程）**：11 个阶段的研究推进，AI 研讨原文**嵌在各阶段之内**（不设附录） |
| `理论从0到1-演进日志.md` | **过程档案（理论线）**：五个改变节点，研讨原文**直接嵌在节点内**（不设附录） |
| `dialogs/ai-dialog-export-*.json` | AI 对话记录导出（由 `ai-dialog-export` 技能生成，文件名含时间戳） |

### `presentation/` —— 小组展示

| 文件 | 说明 |
| --- | --- |
| `小组展示-PPT内容.md` | **展示用（按块累积）**：目前含「A 块·实验设计（细版，11 页，含 6 处思想博弈）」 |
| `小组展示-演讲稿.md` | **展示用（按块累积）**：目前含「A 块·实验设计」的逐页口播稿（约 18 分钟） |

## chat 接力模式（chat-relay）

技能位于 `.reasonix/skills/chat-relay/`：**内容走 chat，运行走执行**——凡需要人理解、讨论、判断、成稿的内容产出（含需独立判定者的锚定判读），改由 ChatGPT 与用户讨论产出；agent 只做备料、表态与实施。判读／编码／计算等可复算的执行性运行不走此通道，由执行侧 skill 直接完成。

开关（在对话中直接发斜杠命令；等价脚本入口见「常用命令」）：

| 命令 | 动作 |
| --- | --- |
| `/chat-relay` | 开启；已开启则报「已是开启状态」 |
| `/chat-relay off` | 关闭（在途会话文件保留） |
| `/chat-relay status` | 只读报告：开关＋在途会话及各自等谁 |

一个 chat 环的标准动作（完整规程：`.reasonix/skills/chat-relay/references/protocol.md`）：

1. **先分析**——读真实工件：本轮要人理解／判断什么、产出要什么形态、不可丢失清单、术语表；
2. **备料**——建会话目录 `topics/<选题>/chat-relay/{YYYY-MM-DD}-{slug}/`：写自包含的 `提示词.md`（chat 不知道仓库的存在）；把它需要的源文件**原样复制**进 `上传包/`（单次上传上限 20 份，超出按同类合卷，不用摘要代替原件）；
3. **交接**——把 `上传包/` 全部拖进 ChatGPT，`提示词.md` 全文贴过去；讨论完把分享链接带回（或把产出存进 `回报/`）；
4. **回程**——贴回 `https://chatgpt.com/share/…` 链接，由 `scripts/fetch-share.py` 直接落盘 `回报/r{N}.md`（格式与伪影说明：`references/chatgpt-share-format.md`）；
5. **表态（必须）**——按保真／事实／可装回三轴核对：同意即按归属 skill 的写入契约实施；反对则写 `提示词-r{N+1}.md` 具体到句，带回 chat；
6. **收敛**——实施完毕，台账记结果，会话收尾。

会话目录（归对应选题，平铺与分组布局通用）：

```
topics/<选题>/chat-relay/{YYYY-MM-DD}-{slug}/
├── 提示词.md        # 贴给 ChatGPT；第二轮起：提示词-r2.md…
├── 上传包/          # F1-简称.md、F2-简称.md…（源文件副本，原件不动）
├── 台账.md          # 状态、材料、轮次、实施记录
└── 回报/            # r1.md、r2.md…（chat 产出落盘）
```

- 开关只由用户命令触发，不自动开启；每轮提醒入口登记在根目录 `AGENTS.md`（等价原 Claude Code 的 UserPromptSubmit 钩子）。
- 开关文件（`chat-relay/ON`）与会话目录（`topics/**/chat-relay/`）为本地工作状态，均不入库（见 `.gitignore`）。

## 工具

| 脚本 | 用途 |
| --- | --- |
| `tools/md2docx.py` | 把 Markdown 转成 Word（需 `pip install python-docx`） |
| `tools/build_report.py` | 合并 `docs/` 下三份源文档（研究设计＋测量工具＋预注册与分析），导出完整版 Word（需 `python-docx`） |
| `tools/build_research_log.py` | 把《全过程日志》里的对话占位符替换为研讨原文，并导出 Word |
| `tools/analysis_pipeline.py` | 分析流水线：计分、信度、t 检验、TOST／贝叶斯因子、并行中介、BH 校正（需 `numpy pandas scipy statsmodels`） |
| `tools/make_figures.py` | 生成 `figures/` 下的三张图（需 `numpy matplotlib`） |
| `tools/dialogs_to_md.py` | 把 AI 对话导出 JSON 转成 Markdown（逐轮保留原文） |

## 常用命令

```bash
# Markdown → Word（输出在仓库根目录）
python3 tools/md2docx.py docs/研究总览.md 研究总览.docx

# 完整版 Word（《研究设计》＋《测量工具》＋《预注册与分析》合并为一份）
python3 tools/build_report.py 研究设计-完整版.docx

# 过程日志 Word（自动嵌入 archive/dialogs/ 中的对话原文）
python3 tools/build_research_log.py

# 展示用图（输出到 figures/）
python3 tools/make_figures.py

# 分析流水线（详见 docs/预注册与分析.md）
python3 tools/analysis_pipeline.py --simulate              # 无数据时先跑通流程（生成 data/simulated.csv）
python3 tools/analysis_pipeline.py --data data/clean.csv   # 有真实数据后（列名见 docs/测量工具.md 计分表）

# AI 对话导出 JSON → Markdown（逐轮原文）
python3 tools/dialogs_to_md.py archive/dialogs/ai-dialog-export-*.json

# chat 接力模式：开关（on / off / status / check）
bash .reasonix/skills/chat-relay/scripts/chat-relay.sh status

# chat 接力模式：回程落盘（ChatGPT 分享链接 → 回报/r{N}.md）
python3 .reasonix/skills/chat-relay/scripts/fetch-share.py "<分享链接>" \
  --drop-prompt "topics/<选题>/chat-relay/{slug}/提示词.md" \
  --output-dir "topics/<选题>/chat-relay/{slug}/回报/"
```

分析产物写入 `outputs/`；`data/`、`outputs/` 与 `*.docx` 均已在 `.gitignore` 中忽略。

## 作者

[@gastby-ghost](https://github.com/gastby-ghost)

## 说明

本仓库为课程作业用途，未声明开源许可证。
