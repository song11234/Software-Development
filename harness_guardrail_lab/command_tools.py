import os
import shlex
import subprocess
import sys
import tempfile

ALLOWED_COMMANDS = {"echo", "date", "wc"}
BLOCKED_OPERATORS = {"|", ">", "<", "`", "$(", "&", ";", "||", "&&"}


class CommandHarnessError(Exception):
    pass


def validate_command(cmd: str) -> list[str]:
    cmd = cmd.strip()
    if not cmd:
        raise CommandHarnessError("命令不能为空")

    for op in BLOCKED_OPERATORS:
        if op in cmd:
            raise CommandHarnessError(f"检测到危险操作符：{op}")

    try:
        parts = shlex.split(cmd)
    except ValueError as e:
        raise CommandHarnessError(f"命令解析失败：{e}")

    if not parts:
        raise CommandHarnessError("命令解析结果为空")

    if parts[0] not in ALLOWED_COMMANDS:
        raise CommandHarnessError(f"不允许的命令：{parts[0]}")

    return parts


def run_command(cmd: str) -> str:
    parts = validate_command(cmd)
    try:
        if sys.platform == "win32":
            # Windows 上 echo 是 cmd 内置命令，需 shell=True + 字符串
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=tempfile.gettempdir(),
                shell=True,
            )
        else:
            result = subprocess.run(
                parts,
                capture_output=True,
                text=True,
                input="",
                timeout=10,
                cwd=tempfile.gettempdir(),
            )
        output = result.stdout.strip()
        if result.stderr:
            output += "\n[stderr] " + result.stderr.strip()
        return output
    except subprocess.TimeoutExpired:
        raise CommandHarnessError("命令执行超时")
