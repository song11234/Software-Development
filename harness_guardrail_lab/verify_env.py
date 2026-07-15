"""
Harness 工程与 Agent 安全护栏 — 环境验证脚本
检查实验目录结构、虚拟环境和依赖是否就绪。
"""
import os
import sys
import platform

BASE = os.path.dirname(os.path.abspath(__file__))
ok_count = 0
fail_count = 0

def check(label, condition, detail=""):
    global ok_count, fail_count
    if condition:
        ok_count += 1
        print(f"  [OK] {label}")
    else:
        fail_count += 1
        print(f"  [FAIL] {label}  {detail}")

print("=" * 55)
print("  HARNESS LAB — 环境验证")
print("=" * 55)

# 1. Python 版本
ver = sys.version_info
check(f"Python 版本: {ver.major}.{ver.minor}.{ver.micro}", ver >= (3, 10),
      f"需要 3.10+，当前 {ver.major}.{ver.minor}")

# 2. 是否在虚拟环境中
in_venv = sys.prefix != sys.base_prefix
check("虚拟环境已激活", in_venv, "建议运行: .venv\\Scripts\\Activate.ps1")

# 3. 目录结构
for d in ["workspace", "blocked", "logs", "safe_file_skill"]:
    full = os.path.join(BASE, d)
    exists = os.path.isdir(full)
    check(f"目录: {d}/", exists)

# 4. 初始文件
for f in ["workspace/note.md", "blocked/secret.txt"]:
    full = os.path.join(BASE, f)
    exists = os.path.isfile(full)
    check(f"文件: {f}", exists)
    if exists:
        with open(full, "r", encoding="utf-8") as fh:
            content = fh.read()
        check(f"  -> 非空: {f}", len(content.strip()) > 0, "文件内容为空")

# 5. pytest
try:
    import pytest
    check(f"pytest {pytest.__version__}", True)
except ImportError:
    check("pytest 已安装", False, "运行: pip install pytest")

# 6. 路径安全问题
blocked_path = os.path.join(BASE, "blocked", "secret.txt")
check("blocked/ 存在于实验目录内", blocked_path.startswith(BASE),
      "工作目录异常")
check("os.cwd 在当前实验目录", os.getcwd().replace("\\", "/") == BASE.replace("\\", "/"),
      f"当前 cwd={os.getcwd()}，建议 cd 到 {BASE}")

print("-" * 55)
print(f"  结果: {ok_count} OK / {fail_count} FAIL")
if fail_count:
    print("  请检查上方 [FAIL] 项目后重新验证。")
else:
    print("  环境就绪，可以开始实验。")
print("=" * 55)
