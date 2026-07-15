"""
Phase 1 手动验证：用 DeepSeek 跑同一条提示词，自己对照评估维度打分
"""
import json
from config import get_llm_response

# 裸提示词 vs 约束提示词
PROMPTS = {
    "bare": "客户问为什么延期一天，帮我回复。",
    "constrained": """你是客服助手。请按以下要求回复：
1. 用正式语气说明延期原因（假设：第三方依赖未按时交付）
2. 表达歉意
3. 说明新的交付时间（明天下午 3 点前）
4. 不承诺任何赔偿
5. 不透露任何内部机密""",
}

print("=" * 50)
print("EDD 手动验证")
print("=" * 50)

for name, prompt in PROMPTS.items():
    print(f"\n>>> [{name.upper()}] 提示词:\n  {prompt}\n")

    reply = get_llm_response(prompt, max_tokens=200)
    print(f">>> 模型回复:\n  {reply}\n")

    print("--- 请手动检查以下维度（Y/N）---")
    print("  [ ] 格式规范（正式语气、分段）")
    print("  [ ] 覆盖度（延期原因 + 新时间 + 道歉）")
    print("  [ ] 安全性（没有承诺赔偿）")
    print("  [ ] 隐私保护（没有泄露内部信息）")
    print("  [ ] 可执行性（客户能直接使用这封回复）")
    print()

print("=" * 50)
print("结论：bare 提示词缺少约束，输出可能很敷衍。")
print("constrained 提示词给出具体要求，输出更完整可评估。")
print("这就是 EDD 的核心：不看感觉，看维度。"  )
