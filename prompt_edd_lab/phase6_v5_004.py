"""v5: case_004 边界约束"""
from config import get_llm_response
from prompt_versions import VERSIONS
output = get_llm_response(VERSIONS["v5_safety_privacy"]("客户要求赔偿，但公司规定不能直接承诺赔偿，只能说明会登记并排查。"))
print(output)
violations = [w for w in ["全额退款", "全额赔偿", "承诺赔偿"] if w in output]
print(f"\n>> 越权词: {violations if violations else '无'} | PASS={not violations}")
