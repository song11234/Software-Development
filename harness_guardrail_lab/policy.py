from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

WORKSPACE_DIR = (BASE_DIR / "workspace").resolve()

LOG_DIR = (BASE_DIR / "logs").resolve()
AUDIT_LOG = LOG_DIR / "audit.jsonl"

ALLOWED_TOOLS = {
    "read_text",
    "write_text",
    "append_text",
    "list_files",
}

ALLOWED_EXTENSIONS = {".txt", ".md", ".json", ".csv"}

MAX_WRITE_CHARS = 2000

# 内容安全策略
SCAN_ON_WRITE = True         # 是否在写入操作前启用内容扫描
BLOCK_ON_SENSITIVE = True     # 发现敏感信息时是否拦截
BLOCK_ON_INJECTION = True     # 发现注入模式时是否拦截

# 网络工具白名单（模块九）
NETWORK_TOOLS = {"fetch_url"}

# 命令工具白名单（模块九）
COMMAND_TOOLS = {"run_command"}
