"""fetch-share.py 离线测试：合成分享页载荷、--drop-prompt 裁除、回报编号顺延。

夹具直接编码 React Router 流载荷（嵌套 JSON，无引用），不依赖网络与真实分享页。
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fetch-share.py"

PROMPT = (
    "# 提示词 — 测试轮\n\n"
    "这是本轮交给 chat 的提示词正文，长度足以作锚定位，内容不会出现在回报里。\n"
    "请基于上传包材料给出改写稿，并列出未决事项。"
)

# 真实回程形态的贴出文本（剪贴板伪影）：标题行未贴、加粗前一字被实体化、
# 标记转义并加倍（源文件：训练只**准备能力** / - **第二条**）
ARTIFACT_FILE = (
    "# 提示词 — 伪影轮\n\n"
    "以下是本轮要点：训练只**准备能力**，不完成关系效力。\n"
    "- **第二条**：把材料读完并列出未决事项，与本轮任务一致，供核对。"
)
ARTIFACT_PASTE = (
    "以下是本轮要点：训练&#x53EA;**\\*\\*准备能力\\*\\***，不完成关系效力。\n"
    "\\- **\\*\\*第二条\\*\\***：把材料读完并列出未决事项，与本轮任务一致，供核对。"
)


def load_module():
    spec = importlib.util.spec_from_file_location("fetch_share", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def msg(role: str, text: str) -> dict[str, Any]:
    # 不带 int/bool 字段：载荷解码器会把裸整数当引用
    return {
        "id": f"m-{role}-{abs(hash(text))}",
        "author": {"role": role},
        "create_time": 1750000000.0,
        "content": {"content_type": "text", "parts": [text]},
    }


def make_html(messages: list[dict[str, Any]]) -> str:
    conversation = {
        "title": "测试会话",
        "create_time": 1750000000.0,
        "update_time": 1750000000.0,
        "linear_conversation": [{"message": m} for m in messages],
    }
    root = {"loaderData": {"routes/share.$shareId": {"serverResponse": {"data": conversation}}}}

    payload: list[Any] = [None, "尾部占位"]
    # 布尔按真实编码走引用：扁平数组里放 true 本体，字典里放它的索引
    # （解码器把 dict/list 中的裸 int 一律当引用，Python 的 bool 是 int 子类）
    def index_bools(value: Any) -> Any:
        if isinstance(value, bool):
            payload.append(value)
            return len(payload) - 1
        if isinstance(value, dict):
            return {k: index_bools(v) for k, v in value.items()}
        if isinstance(value, list):
            return [index_bools(v) for v in value]
        return value

    payload[0] = index_bools(root)
    blob = json.dumps(payload, ensure_ascii=False)
    literal = json.dumps(blob, ensure_ascii=False)
    return (
        "<html><body><script>"
        f"window.__reactRouterContext.streamController.enqueue({literal});"
        "</script></body></html>"
    )


def prepare(tmp_path: Path, monkeypatch, messages: list[dict[str, Any]]) -> tuple[Any, Path]:
    module = load_module()
    monkeypatch.setenv("CHAT_RELAY_ROOT", str(tmp_path))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "")
    html_file = tmp_path / "page.html"
    html_file.write_text(make_html(messages), encoding="utf-8")
    return module, html_file


def test_converts_synthetic_share_page(tmp_path: Path, monkeypatch, capsys) -> None:
    module, html_file = prepare(
        tmp_path,
        monkeypatch,
        [
            msg("user", PROMPT),
            msg("tool", "插件输出被隐去。"),
            msg("assistant", "这是回答正文。"),
        ],
    )
    out = tmp_path / "out.md"
    assert module.main([str(html_file), "-o", str(out)]) == 0

    text = out.read_text(encoding="utf-8")
    assert "# 测试会话" in text
    assert "- Fetched:" in text
    assert PROMPT in text
    assert "## 1. User" in text
    assert "## 2. Assistant" in text
    assert "插件输出被隐去" not in text  # 工具轮默认不落


def test_drop_prompt_trims_and_numbers_rounds(tmp_path: Path, monkeypatch) -> None:
    module, html_file = prepare(
        tmp_path,
        monkeypatch,
        [
            msg("user", PROMPT),
            msg("assistant", "第一轮回答。"),
            msg("user", "追问一句。"),
            msg("assistant", "追问后的回答。"),
        ],
    )
    prompt_file = tmp_path / "提示词.md"
    prompt_file.write_text(PROMPT, encoding="utf-8")
    ret_dir = tmp_path / "回报"

    assert module.main(
        [str(html_file), "--drop-prompt", str(prompt_file), "--output-dir", str(ret_dir)]
    ) == 0
    first = (ret_dir / "r1.md").read_text(encoding="utf-8")
    assert PROMPT not in first
    assert "第一轮回答。" in first
    assert "追问一句。" in first
    assert "追问后的回答。" in first
    assert "- 裁除：提示词.md" in first

    # 再落一次：编号顺延 r2
    assert module.main(
        [str(html_file), "--drop-prompt", str(prompt_file), "--output-dir", str(ret_dir)]
    ) == 0
    assert (ret_dir / "r2.md").exists()


def test_drop_prompt_miss_fails_without_writing(tmp_path: Path, monkeypatch, capsys) -> None:
    module, html_file = prepare(tmp_path, monkeypatch, [msg("user", PROMPT), msg("assistant", "回答。")])
    prompt_file = tmp_path / "提示词.md"
    prompt_file.write_text(
        "这一整段文字与本轮提示词毫无关系，专门用来测试未命中路径的报错行为，确认失败时不会写出任何回报文件。",
        encoding="utf-8",
    )
    ret_dir = tmp_path / "回报"

    assert module.main(
        [str(html_file), "--drop-prompt", str(prompt_file), "--output-dir", str(ret_dir)]
    ) == 1
    assert "旧快照" in capsys.readouterr().err
    assert not (ret_dir / "r1.md").exists()


def test_drop_leaves_nothing_fails(tmp_path: Path, monkeypatch, capsys) -> None:
    module, html_file = prepare(tmp_path, monkeypatch, [msg("user", PROMPT)])
    prompt_file = tmp_path / "提示词.md"
    prompt_file.write_text(PROMPT, encoding="utf-8")

    assert module.main(
        [str(html_file), "--drop-prompt", str(prompt_file), "-o", str(tmp_path / "out.md")]
    ) == 1
    assert "没有新增内容" in capsys.readouterr().err
    assert not (tmp_path / "out.md").exists()


def test_output_and_output_dir_are_mutually_exclusive(tmp_path: Path, monkeypatch, capsys) -> None:
    module, html_file = prepare(tmp_path, monkeypatch, [msg("user", PROMPT), msg("assistant", "回答。")])

    assert module.main(
        [str(html_file), "-o", str(tmp_path / "a.md"), "--output-dir", str(tmp_path / "d")]
    ) == 1
    assert "只能给其一" in capsys.readouterr().err


def test_drop_tolerates_clipboard_artifacts(tmp_path: Path, monkeypatch) -> None:
    module, html_file = prepare(
        tmp_path,
        monkeypatch,
        [msg("user", ARTIFACT_PASTE), msg("assistant", "伪影轮回答。")],
    )
    prompt_file = tmp_path / "提示词.md"
    prompt_file.write_text(ARTIFACT_FILE, encoding="utf-8")
    ret_dir = tmp_path / "回报"

    assert module.main(
        [str(html_file), "--drop-prompt", str(prompt_file), "--output-dir", str(ret_dir)]
    ) == 0
    out = (ret_dir / "r1.md").read_text(encoding="utf-8")
    assert "伪影轮回答。" in out
    assert "准备能力" not in out  # 提示词整段被裁，伪影不进回报


def test_redacted_messages_are_skipped(tmp_path: Path, monkeypatch) -> None:
    shell = msg("assistant", "The output of this plugin was redacted.")
    shell["metadata"] = {"is_redacted": True}
    redacted_tool = msg("tool", "The output of this plugin was redacted.")
    redacted_tool["metadata"] = {"is_redacted": True}
    module, html_file = prepare(
        tmp_path,
        monkeypatch,
        [msg("user", "问题正文。"), redacted_tool, shell, msg("assistant", "真正的回答。")],
    )
    out = tmp_path / "out.md"

    assert module.main([str(html_file), "-o", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "plugin was redacted" not in text  # 正文里不留隐去壳（路径里可能含测试名，故匹配全文特征串）
    assert "真正的回答。" in text
    assert "## 2. Assistant" in text  # 编号跳过被隐去的壳
