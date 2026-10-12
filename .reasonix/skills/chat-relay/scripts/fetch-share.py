#!/usr/bin/env python3
"""Convert a public ChatGPT share link (or saved share HTML) into Markdown."""

# ---------------------------------------------------------------------------
# Vendored from chatgpt-share-md — https://github.com/schneiderjoseph/chatgpt-share-md
# (本文件取自其 plugins/chatgpt-share-md/bin/chatgpt_share_md.py，逐字节保留)
#
# 本仓库改动（chat-relay 回程接线，2026-10-12）：
#   1. 读仓库根 .env 的代理配置（终端已有环境变量优先）；
#   2. 新增 --drop-prompt：从本轮提示词所在用户消息之后开始落盘——提示词与前轮
#      已确认内容裁除，避免多轮重复堆积；提示词匹配不到即报错（通常说明链接是旧快照）；
#   3. 新增 --output-dir：自动顺延写 回报/r{N}.md（回报文件只由本脚本落盘，
#      agent 不再二次写入）；
#   4. 文件头增加 Fetched 与裁除说明两行；
#   5. 跳过分享页隐去的消息（metadata.is_redacted：工具轮与工具调用壳）；
#   6. 提示词匹配按归一相似度判定，容忍剪贴板伪影（实体化字符、转义/加倍标记）。
#
# MIT License
#
# Copyright (c) 2026 Schneider Joseph
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ---------------------------------------------------------------------------

from __future__ import annotations

import argparse
import ast
import datetime as dt
import difflib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache
from pathlib import Path
from typing import Any

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

ROLE_HEADINGS = {
    "user": "User",
    "assistant": "Assistant",
    "system": "System",
    "tool": "Tool",
}

# ChatGPT embeds interactive widgets with private-use Unicode delimiters.
WIDGET_RE = re.compile(
    "\ue200(?P<kind>[^\ue202]+)\ue202(?P<payload>.*?)\ue201",
    re.DOTALL,
)


class ConvertError(RuntimeError):
    """Raised when a share page cannot be converted."""


def is_url(source: str) -> bool:
    return urllib.parse.urlparse(source).scheme in {"http", "https"}


def normalize_share_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    host = (parsed.netloc or "").lower()
    path = parsed.path or ""

    if host in {"chatgpt.com", "www.chatgpt.com", "chat.openai.com", "www.chat.openai.com"}:
        if "/share/" in path:
            return urllib.parse.urlunparse(
                ("https", host.removeprefix("www."), path, "", "", "")
            )

    raise ConvertError(
        "Expected a public ChatGPT share URL like "
        "https://chatgpt.com/share/<id>"
    )


def fetch_html(url: str, timeout: int) -> str:
    url = normalize_share_url(url)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        raise ConvertError(f"HTTP {exc.code} while fetching {url}") from exc
    except urllib.error.URLError as exc:
        raise ConvertError(f"Could not fetch URL: {exc.reason}") from exc


def read_source(source: str, timeout: int) -> tuple[str, str | None]:
    if is_url(source):
        url = normalize_share_url(source)
        return fetch_html(url, timeout), url

    path = Path(source).expanduser().resolve()
    if not path.is_file():
        raise ConvertError(f"File not found: {path}")
    return path.read_text(encoding="utf-8", errors="replace"), None


def project_root() -> Path:
    """仓库根：CHAT_RELAY_ROOT > CLAUDE_PROJECT_DIR > 脚本位置上溯四级。"""
    for key in ("CHAT_RELAY_ROOT", "CLAUDE_PROJECT_DIR"):
        value = os.environ.get(key)
        if value:
            return Path(value).expanduser().resolve()
    return Path(__file__).resolve().parents[4]


def load_project_env() -> None:
    """把仓库根 .env 注入环境（终端已有变量优先；缺文件或 dotenv 时静默跳过）。"""
    env_path = project_root() / ".env"
    if not env_path.is_file():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(env_path, override=False)


def normalize_for_match(text: str) -> str:
    """相似度匹配用归一：解码实体、去转义与强调标记、去空白。

    从渲染页复制粘贴的文本常带伪影：加粗标记前一字被实体化（只 → &#x53EA;）、
    标记本身被转义或加倍（- → \\- 、**…** → **\\*\\*…\\*\\*** ）。匹配时一概忽略，
    只比对文字本体。"""
    text = re.sub(r"&#x([0-9A-Fa-f]+);", lambda m: chr(int(m.group(1), 16)), text)
    text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!>~|])", r"\1", text)
    text = re.sub(r"[*_`]", "", text)
    return re.sub(r"\s+", "", text)


def drop_before_prompt(
    messages: list[dict[str, Any]], prompt_path: Path
) -> list[dict[str, Any]]:
    """裁除本轮提示词及其之前的轮次：返回提示词所在用户消息之后的消息。

    贴进 chat 的文本与提示词文件常有出入（首部的标题与「用法」行不贴、剪贴板
    转义与实体伪影），因此按归一后的相似度判定，而不是逐字匹配。整条会话里都
    找不到足够相似的消息时报错——通常说明链接还是旧快照（未含本轮）或提示词
    尚未贴出。"""
    if not prompt_path.is_file():
        raise ConvertError(f"提示词文件不存在：{prompt_path}")

    target = normalize_for_match(prompt_path.read_text(encoding="utf-8"))
    if len(target) < 50:
        raise ConvertError(f"提示词过短，无法作锚定位：{prompt_path}")

    for index, message in enumerate(messages):
        if message["role"] != "user":
            continue
        candidate = normalize_for_match(message["content"])
        if len(candidate) < 50:
            continue
        matcher = difflib.SequenceMatcher(None, target, candidate, autojunk=False)
        if matcher.quick_ratio() < 0.6:
            continue
        if matcher.ratio() >= 0.85:
            return messages[index + 1 :]

    raise ConvertError(
        "本轮提示词在会话记录里找不到足够相似的贴出消息：分享链接可能还是旧快照"
        "（未含本轮），或提示词尚未贴出。确认后重试。"
    )


def next_round_output(output_dir: Path) -> Path:
    """回报/r{N}.md：在既有 r*.md 之后顺延（回报文件只由本脚本落盘）。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    numbers = [
        int(match.group(1))
        for path in output_dir.glob("r*.md")
        if (match := re.fullmatch(r"r(\d+)\.md", path.name))
    ]
    return output_dir / f"r{max(numbers, default=0) + 1}.md"


def extract_stream_chunks(html: str) -> list[str]:
    pattern = re.compile(
        r"window\.__reactRouterContext\.streamController\.enqueue\("
        r"(?P<literal>\"(?:\\.|[^\"\\])*\")"
        r"\);",
        re.DOTALL,
    )
    chunks: list[str] = []
    for match in pattern.finditer(html):
        literal = match.group("literal")
        try:
            chunks.append(json.loads(literal))
        except json.JSONDecodeError:
            try:
                chunks.append(ast.literal_eval(literal))
            except (SyntaxError, ValueError) as exc:
                raise ConvertError("Could not decode a React stream chunk.") from exc

    if chunks:
        return chunks

    # Legacy Next.js shares
    next_data = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(?P<data>.*?)</script>',
        html,
        re.DOTALL,
    )
    if next_data:
        return [next_data.group("data")]

    raise ConvertError(
        "No ChatGPT conversation payload found. "
        "The share may be private, expired, blocked, or require login. "
        "Tip: open the share link in a private window, save the page as HTML, "
        "then pass that file to this tool."
    )


def load_indexed_payload(chunks: list[str]) -> list[Any] | dict[str, Any]:
    for chunk in chunks:
        text = chunk.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, list) and payload:
            return payload
        if isinstance(payload, dict):
            return payload
    raise ConvertError("No JSON conversation payload found in the page.")


def resolve_indexed_payload(payload: list[Any]) -> Any:
    resolving: set[int] = set()

    @lru_cache(maxsize=None)
    def resolve_index(index: int) -> Any:
        if index < 0:
            return None
        if index >= len(payload):
            raise ConvertError(f"Payload reference out of range: {index}")
        if index in resolving:
            return "…"
        resolving.add(index)
        try:
            return resolve_value(payload[index])
        finally:
            resolving.remove(index)

    def resolve_value(value: Any) -> Any:
        if isinstance(value, dict):
            resolved: dict[Any, Any] = {}
            for raw_key, raw_value in value.items():
                if (
                    isinstance(raw_key, str)
                    and raw_key.startswith("_")
                    and raw_key[1:].lstrip("-").isdigit()
                ):
                    key = resolve_index(int(raw_key[1:]))
                else:
                    key = raw_key
                val = (
                    resolve_index(raw_value)
                    if isinstance(raw_value, int)
                    else resolve_value(raw_value)
                )
                resolved[key] = val
            return resolved

        if isinstance(value, list):
            return [
                resolve_index(item) if isinstance(item, int) else resolve_value(item)
                for item in value
            ]
        return value

    return resolve_index(0)


def find_shared_conversation(root: Any) -> dict[str, Any]:
    # Modern React Router share pages
    if isinstance(root, dict) and "loaderData" in root:
        loader_data = root["loaderData"]
        if isinstance(loader_data, dict):
            for route_data in loader_data.values():
                if not isinstance(route_data, dict):
                    continue
                response = route_data.get("serverResponse")
                if not isinstance(response, dict):
                    continue
                data = response.get("data")
                if isinstance(data, dict) and "linear_conversation" in data:
                    return data

    # Legacy __NEXT_DATA__
    if isinstance(root, dict):
        props = root.get("props", {})
        page_props = props.get("pageProps", {}) if isinstance(props, dict) else {}
        server_response = (
            page_props.get("serverResponse", {})
            if isinstance(page_props, dict)
            else {}
        )
        data = (
            server_response.get("data")
            if isinstance(server_response, dict)
            else None
        )
        if isinstance(data, dict) and "linear_conversation" in data:
            return data

    raise ConvertError("Could not find linear_conversation in the share payload.")


def clean_widget(kind: str, payload: str) -> str:
    kind = kind.strip()
    payload = payload.strip()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        data = None

    if kind == "entity" and isinstance(data, list) and len(data) >= 2:
        return str(data[1])

    if kind == "image_group":
        # Visual carousels are not downloadable from the share payload alone.
        return ""

    if kind in {"cite", "citation", "tether", "navigation"}:
        return ""

    return ""


def sanitize_text(text: str) -> str:
    cleaned = WIDGET_RE.sub(
        lambda match: clean_widget(match.group("kind"), match.group("payload")),
        text,
    )
    # Remove any leftover private-use markers.
    cleaned = re.sub("[\ue200-\ue202]", "", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def render_part(part: Any) -> str:
    if part is None:
        return ""
    if isinstance(part, str):
        return sanitize_text(part)
    if isinstance(part, dict):
        for key in ("text", "content", "transcript"):
            value = part.get(key)
            if isinstance(value, str):
                return sanitize_text(value)
        # Image / file references
        asset_pointer = part.get("asset_pointer") or part.get("url")
        if isinstance(asset_pointer, str):
            filename = part.get("metadata", {})
            name = ""
            if isinstance(filename, dict):
                name = filename.get("name") or ""
            label = name or "attachment"
            return f"![{label}]({asset_pointer})"
        return ""
    return str(part)


def extract_messages(
    conversation: dict[str, Any],
    *,
    include_tools: bool,
    include_system: bool,
) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    nodes = conversation.get("linear_conversation") or []

    for node in nodes:
        if not isinstance(node, dict):
            continue
        message = node.get("message")
        if not isinstance(message, dict):
            continue

        author = message.get("author") or {}
        role = author.get("role") or author.get("name") or "unknown"
        if role == "tool" and not include_tools:
            continue
        if role == "system" and not include_system:
            continue

        # 分享页隐去的消息没有内容（工具轮与工具调用壳），一律不落
        metadata = message.get("metadata") or {}
        if isinstance(metadata, dict) and metadata.get("is_redacted"):
            continue

        content = message.get("content") or {}
        parts = content.get("parts") or []
        text = "\n".join(
            rendered
            for rendered in (render_part(part).strip() for part in parts)
            if rendered
        ).strip()
        if not text:
            continue

        messages.append(
            {
                "role": role,
                "content": text,
                "created_at": message.get("create_time"),
            }
        )

    return messages


def format_timestamp(timestamp: Any) -> str | None:
    if not isinstance(timestamp, (int, float)):
        return None
    return (
        dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def slugify(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title, flags=re.UNICODE)
    slug = re.sub(r"[-\s]+", "-", slug).strip("-").lower()
    return slug[:80] or "chatgpt-conversation"


def role_heading(role: str) -> str:
    return ROLE_HEADINGS.get(role, role.replace("_", " ").title())


def build_markdown(
    conversation: dict[str, Any],
    messages: list[dict[str, Any]],
    source: str | None,
    extra_meta: list[str] | None = None,
) -> str:
    title = conversation.get("title") or "ChatGPT conversation"
    lines: list[str] = [f"# {title}", ""]

    meta: list[str] = []
    if source:
        meta.append(f"- Source: {source}")
    conversation_id = conversation.get("conversation_id")
    if conversation_id:
        meta.append(f"- Conversation ID: `{conversation_id}`")
    created = format_timestamp(conversation.get("create_time"))
    updated = format_timestamp(conversation.get("update_time"))
    if created:
        meta.append(f"- Created: {created}")
    if updated:
        meta.append(f"- Updated: {updated}")
    meta.append(f"- Messages: {len(messages)}")
    if extra_meta:
        meta.extend(extra_meta)
    lines.extend(meta)
    lines.append("")

    for index, message in enumerate(messages, start=1):
        lines.append(f"## {index}. {role_heading(message['role'])}")
        lines.append("")
        lines.append(message["content"])
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def default_output_path(conversation: dict[str, Any], output_dir: Path) -> Path:
    title = conversation.get("title") or "chatgpt-conversation"
    return output_dir / f"{slugify(title)}.md"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a public ChatGPT share URL (or saved share HTML) "
            "into a Markdown document."
        )
    )
    parser.add_argument(
        "source",
        help="ChatGPT share URL or path to a saved share-page HTML file",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output .md path (default: <slugified-title>.md in the current directory)",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print Markdown to stdout instead of writing a file",
    )
    parser.add_argument(
        "--include-tools",
        action="store_true",
        help="Include tool/plugin messages (skipped by default)",
    )
    parser.add_argument(
        "--include-system",
        action="store_true",
        help="Include system messages (skipped by default)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Also write a sibling .json file with structured messages",
    )
    parser.add_argument(
        "--drop-prompt",
        help="本轮提示词文件：从其所在用户消息之后开始落盘（裁除提示词与前轮已确认部分）",
    )
    parser.add_argument(
        "--output-dir",
        help="输出目录：自动顺延写入 r{N}.md（与 --output 互斥）",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP timeout in seconds (default: 30)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    try:
        load_project_env()

        if args.output and args.output_dir:
            raise ConvertError("--output 与 --output-dir 只能给其一。")

        html, source_url = read_source(args.source, args.timeout)
        chunks = extract_stream_chunks(html)
        payload = load_indexed_payload(chunks)
        root = (
            resolve_indexed_payload(payload)
            if isinstance(payload, list)
            else payload
        )
        conversation = find_shared_conversation(root)
        messages = extract_messages(
            conversation,
            include_tools=args.include_tools,
            include_system=args.include_system,
        )
        if not messages:
            raise ConvertError("Conversation payload found, but it contained no messages.")

        extra_meta = [
            "- Fetched: "
            + dt.datetime.now(tz=dt.timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        ]
        if args.drop_prompt:
            drop_path = Path(args.drop_prompt).expanduser()
            messages = drop_before_prompt(messages, drop_path)
            extra_meta.append(
                f"- 裁除：{drop_path.name} 及其之前的轮次（已确认部分不重复落盘）"
            )
            if not messages:
                raise ConvertError(
                    "裁除后没有新增内容：对话在提示词之后还没有产出（或链接是旧快照）。"
                )

        markdown = build_markdown(
            conversation, messages, source_url or args.source, extra_meta
        )

        if args.stdout:
            sys.stdout.write(markdown)
            return 0

        if args.output:
            out_path = Path(args.output).expanduser().resolve()
        elif args.output_dir:
            out_path = next_round_output(Path(args.output_dir).expanduser().resolve())
        else:
            out_path = default_output_path(conversation, Path.cwd())

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(markdown, encoding="utf-8")
        print(f"Wrote {out_path} ({len(messages)} messages)")

        if args.json:
            json_path = out_path.with_suffix(".json")
            document = {
                "title": conversation.get("title"),
                "source": source_url or args.source,
                "conversation_id": conversation.get("conversation_id"),
                "created_at": format_timestamp(conversation.get("create_time")),
                "updated_at": format_timestamp(conversation.get("update_time")),
                "messages": messages,
            }
            json_path.write_text(
                json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"Wrote {json_path}")

        return 0
    except ConvertError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def run() -> None:
    """Console-script entry point."""
    raise SystemExit(main())


if __name__ == "__main__":
    run()
