#!/usr/bin/env python3
"""把 ai-dialog-export-*.json 转成 Markdown（逐轮保留原文）。

用法
    # 输出到标准输出
    python3 tools/dialogs_to_md.py ai-dialog-export-*.json

    # 输出到文件
    python3 tools/dialogs_to_md.py -o 对话原文.md ai-dialog-export-*.json

    # 追加到某文件（用于拼装日志的附录）
    python3 tools/dialogs_to_md.py ai-dialog-export-*.json >> 理论从0到1-演进日志.md

说明
    - 多处 JSON 按文件名顺序输出（文件名含时间戳，即时间顺序）。
    - 原文里行首的 `#` 会被改写为**加粗段落**，避免打乱宿主文档的标题层级；
      表格、加粗、引用等行内语法保持原样，仍可正常渲染。
"""
import argparse
import glob
import json
import os
import re
import sys


def esc_heading(text):
    """把原文的行首标题改写为加粗段落，避免打乱宿主文档的标题层级。"""
    return "\n".join(re.sub(r"^#{1,6}\s+(.*)$", r"**\1**", ln) for ln in text.split("\n"))


def render(path, idx, level=3, turns=None):
    """把一份导出渲染为 Markdown。

    level —— 「记录」标题的层级（轮次低一级）
    turns —— 只渲染这些轮次（None = 全部）。为 None 时输出「记录」抬头，
             指定轮次时只输出轮次块，便于把不同轮次摆到正文的不同位置。
    """
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    m = d.get("session_meta", {})
    h1, h2 = "#" * level, "#" * (level + 1)
    all_turns = d.get("turns", [])
    out = []
    if turns is None:
        sel = all_turns
        out += [
            f"{h1} 记录 {idx}｜{m.get('stage', '—')} 阶段（{len(all_turns)} 轮）",
            "",
            f"- 平台：{m.get('platform', '—')}　模型：{m.get('model', '—')}　导出时间：{m.get('export_time', '—')}",
            f"- 主题：{m.get('topic', '—')}　源文件：`{os.path.basename(path)}`",
            "",
        ]
    else:
        sel = [t for t in all_turns if t.get("turn") in turns]
    for t in sel:
        out += [f"{h2} 轮 {t.get('turn')}｜用户", "", esc_heading(t.get("user_text", "").strip()), ""]
        out += [f"{h2} 轮 {t.get('turn')}｜AI", "", esc_heading(t.get("assistant_text", "").strip()), ""]
        if t.get("actions"):
            out += [f"*Actions：{' / '.join(t['actions'])}*", ""]
        if t.get("turning_point"):
            out += ["*（本次被标注为关键转折点）*", ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="把 AI 对话导出 JSON 转成 Markdown")
    ap.add_argument("files", nargs="+", help="ai-dialog-export-*.json")
    ap.add_argument("-o", "--out", help="输出文件（缺省则打印到标准输出）")
    args = ap.parse_args()

    paths = []
    for p in args.files:
        paths.extend(sorted(glob.glob(p)) or [p])

    text = "\n\n".join(render(p, i) for i, p in enumerate(paths, 1))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print(f"已写入 {args.out}（{len(paths)} 份记录，{len(text)} 字）", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
