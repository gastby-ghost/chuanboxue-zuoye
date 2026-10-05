#!/usr/bin/env python3
"""把《研究设计》《测量工具》《预注册与分析》合并导出为一份完整 Word。

用法
    python3 tools/build_report.py [输出文件名]
    # 默认输出：研究设计-完整版.docx

依赖
    python3 -m pip install python-docx

说明
    三份 .md 仍是各自的源文件；本脚本只做合并导出，不改动源文件。
    正文中的图片按相对仓库根目录的路径解析（`模型图.png`、`figures/*.png`）。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md2docx  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PARTS = [
    ("研究设计.md", "第一部分　研究设计"),
    ("测量工具.md", "第二部分　测量工具：问卷与编码手册"),
    ("预注册与分析.md", "第三部分　预注册与分析方案"),
]

PREAMBLE = """# 研究设计（完整版）

> 本报告由仓库中三份源文档合并导出，内容与源文件一致。

| 部分 | 源文件 | 内容 |
| --- | --- | --- |
| 第一部分 | `研究设计.md` | 研究问题、模型与假设、操作化、刺激材料、实验设计、样本与检验力、分析策略、效度局限 |
| 第二部分 | `测量工具.md` | 问卷题项全文、计分表、编码手册、伦理与知情同意 |
| 第三部分 | `预注册与分析.md` | 预注册模板、检验力、判定规则、SPSS/PROCESS 操作 |

> 正文中提到的《测量工具.md》《预注册与分析.md》，即本报告的第二、第三部分。
"""


def demote(md):
    """把每个标题降一级，使各部分纳入统一的分节标题之下。"""
    return "\n".join("#" + ln if re.match(r"^#{1,6}\s", ln) else ln
                     for ln in md.split("\n"))


def main():
    out_name = sys.argv[1] if len(sys.argv) > 1 else "研究设计-完整版.docx"
    chunks = [PREAMBLE]
    for fn, title in PARTS:
        with open(os.path.join(ROOT, fn), encoding="utf-8") as fh:
            chunks.append(f"# {title}\n\n" + demote(fh.read()))
    merged = "\n\n".join(chunks)

    tmp = os.path.join(ROOT, "_merge_tmp.md")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(merged)
    try:
        md2docx.convert(tmp, os.path.join(ROOT, out_name))
    finally:
        os.remove(tmp)


if __name__ == "__main__":
    main()
