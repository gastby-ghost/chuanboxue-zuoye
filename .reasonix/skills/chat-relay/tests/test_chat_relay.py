"""chat-relay 脚本测试：开关三态、钩子注入与静默、会话清点。"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "chat-relay.sh"
ON = "chat-relay/ON"


def run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "CHAT_RELAY_ROOT": str(root), "CLAUDE_PROJECT_DIR": ""}
    return subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True, env=env)


def test_default_off_and_silent_hook(tmp_path: Path) -> None:
    assert "关闭" in run(tmp_path, "status").stdout
    hook = run(tmp_path, "check")
    assert hook.returncode == 0
    assert hook.stdout.strip() == ""


def test_on_off_cycle(tmp_path: Path) -> None:
    on = run(tmp_path, "on")
    assert on.returncode == 0
    assert (tmp_path / ON).exists()
    assert "开启" in run(tmp_path, "status").stdout

    hook = run(tmp_path, "check")
    assert hook.returncode == 0
    assert "chat-relay" in hook.stdout and "表态" in hook.stdout

    off = run(tmp_path, "off")
    assert off.returncode == 0
    assert not (tmp_path / ON).exists()
    assert run(tmp_path, "check").stdout.strip() == ""


def test_status_lists_open_sessions(tmp_path: Path) -> None:
    session = tmp_path / "topics" / "demo-topic" / "chat-relay" / "2026-01-01-demo"
    session.mkdir(parents=True)
    (session / "台账.md").write_text("# 台账\n\n- 状态：待表态\n", encoding="utf-8")
    run(tmp_path, "on")
    out = run(tmp_path, "status").stdout
    assert "demo-topic/2026-01-01-demo" in out
    assert "待表态" in out


def test_status_finds_grouped_topic_sessions(tmp_path: Path) -> None:
    session = tmp_path / "topics" / "group-a" / "demo-topic" / "chat-relay" / "2026-01-02-demo"
    session.mkdir(parents=True)
    (session / "台账.md").write_text("# 台账\n\n- 状态：等带回\n", encoding="utf-8")
    run(tmp_path, "on")
    out = run(tmp_path, "status").stdout
    assert "demo-topic/2026-01-02-demo" in out
    assert "等带回" in out


def test_root_workspace_session_not_listed(tmp_path: Path) -> None:
    # 会话归选题：放回根 chat-relay/ 的旧位置不被列出（不留兼容）
    stray = tmp_path / "chat-relay" / "2026-01-01-stray"
    stray.mkdir(parents=True)
    (stray / "台账.md").write_text("- 状态：等带去\n", encoding="utf-8")
    run(tmp_path, "on")
    out = run(tmp_path, "status").stdout
    assert "stray" not in out


def test_unknown_command_fails(tmp_path: Path) -> None:
    r = run(tmp_path, "bogus")
    assert r.returncode == 2
