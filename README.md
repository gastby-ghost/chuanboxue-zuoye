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
```

分析产物写入 `outputs/`；`data/`、`outputs/` 与 `*.docx` 均已在 `.gitignore` 中忽略。

## 作者

[@gastby-ghost](https://github.com/gastby-ghost)

## 说明

本仓库为课程作业用途，未声明开源许可证。
