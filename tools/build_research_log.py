#!/usr/bin/env python3
"""把《研究从 0 到 1：全过程日志》里的对话占位符替换为原文，并导出 Word。

用法
    python3 tools/build_research_log.py [输出.docx] [--source 源.md]
    # 缺省：源 = 研究从0到1-全过程日志.md，输出 = 同名 .docx

    # 例：生成理论演进日志
    python3 tools/build_research_log.py --source 理论从0到1-演进日志.md 理论从0到1-演进日志.docx

原理
    源文件 `研究从0到1-全过程日志.md` 在需要嵌入对话的位置留有占位符
    `<!--DIALOG:n-->`，n 为 `ai-dialog-export-*.json` 按文件名排序后的序号
    （文件名含时间戳，即研讨的时间顺序）。本脚本把对应记录的**全部轮次原文**
    嵌进去，再交给 md2docx 导出 Word；源文件本身保持不含原文。

依赖
    python3 -m pip install python-docx
"""
import argparse
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import md2docx        # noqa: E402
import dialogs_to_md  # noqa: E402

ROOT = os.path.dirname(HERE)
LEVEL = 3  # 嵌入后的「记录」标题用三级，轮次用四级


def main():
    ap = argparse.ArgumentParser(description="把带对话占位符的日志 md 导出为 Word")
    ap.add_argument("out", nargs="?", default="研究从0到1-全过程日志.docx",
                    help="输出 .docx（缺省：研究从0到1-全过程日志.docx）")
    ap.add_argument("--source", default="研究从0到1-全过程日志.md",
                    help="源 md（含 <!--DIALOG:n--> 占位符）")
    args = ap.parse_args()

    source = os.path.join(ROOT, args.source)
    dialogs = sorted(glob.glob(os.path.join(ROOT, "ai-dialog-export-*.json")))
    index = {i: p for i, p in enumerate(dialogs, 1)}

    with open(source, encoding="utf-8") as fh:
        text = fh.read()

    used, missing = [], []

    def repl(m):
        n = int(m.group(1))
        if n not in index:
            missing.append(n)
            return f"> （缺第 {n} 份对话记录，请确认 `ai-dialog-export-*.json` 是否齐全）"
        used.append(n)
        return dialogs_to_md.render(index[n], n, level=LEVEL)

    text = re.sub(r"<!--DIALOG:(\d+)-->", repl, text)

    if missing:
        print(f"警告：占位符引用了不存在的记录 {missing}", file=sys.stderr)
    print(f"源文件：{args.source}｜已嵌入 {len(used)} 份对话记录：{used}", file=sys.stderr)

    tmp = os.path.join(ROOT, "_research_log_tmp.md")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    try:
        md2docx.convert(tmp, os.path.join(ROOT, args.out))
    finally:
        os.remove(tmp)


if __name__ == "__main__":
    main()
