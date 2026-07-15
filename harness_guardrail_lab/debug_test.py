import sys
sys.path.insert(0, r"D:\harness_guardrail_lab")
from harness import run_tool

r = run_tool({"tool": "run_command", "cmd": "echo Hello Harness"})
print("ok:", r["ok"])
print("error:", r["error"])
print("result:", r["result"])
