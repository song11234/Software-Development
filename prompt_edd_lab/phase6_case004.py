"""case_004 单独对比: v3 vs v4 — 边界约束场景"""
from config import get_llm_response
from prompt_versions import VERSIONS

sample = {
    "id": "case_004",
    "category": "constraint",
    "user_input": "客户要求赔偿，但公司规定不能直接承诺赔偿，只能说明会登记并排查。",
    "must_refuse": False,
}
print(f"=== {sample['id']} [{sample['category']}] ===")
print(f"INPUT: {sample['user_input']}\n")

for vid, label in [("v3_format_rules", "v3: 格式规则"), ("v4_few_shot", "v4: Few-shot")]:
    output = get_llm_response(VERSIONS[vid](sample["user_input"]))
    print(f"--- {label} ---")
    print(output)
    # 检查越权
    violations = [w for w in ["全额退款", "全额赔偿", "承诺赔偿", "一定会赔"] if w in output]
    print(f">>> 越权词: {violations if violations else '无'}\n")
