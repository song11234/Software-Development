"""
Phase 5 直观观察：v1 vs v3 原始输出对比

选 3 条代表性样本，并排查看原始回复，
不做评分——直接看结构、语气、边界意识的变化。
"""

from config import get_llm_response
from samples import SAMPLES
from prompt_versions import VERSIONS

# 挑 3 条最有代表性的样本
FOCUS_SAMPLES = ["case_001", "case_004", "case_006"]


def run_one(version_id, sample):
    prompt_fn = VERSIONS[version_id]
    prompt = prompt_fn(sample["user_input"])
    return get_llm_response(prompt)


def main():
    versions = [
        ("v1_baseline", "基    线：几乎无约束"),
        ("v3_format_rules", "改    进：角色 + 栏目 + 边界规则"),
    ]

    focus = [s for s in SAMPLES if s["id"] in FOCUS_SAMPLES]

    for sample in focus:
        print("=" * 70)
        print(f"  {sample['id']}  [{sample['category']}]")
        print(f"  输入: {sample['user_input']}")
        print("=" * 70)

        results = {}
        for vid, label in versions:
            print(f"\n  >>> {label} <<<")
            output = run_one(vid, sample)
            results[vid] = output
            print(f"  {'─' * 66}")
            # 缩进打印输出
            for line in output.split("\n"):
                print(f"  | {line}")
            print(f"  {'─' * 66}")

        # 快速标注差异
        print(f"\n  >> 快速对比：")
        v1 = results["v1_baseline"]
        v3 = results["v3_format_rules"]

        # 结构检查
        has_section_v1 = "回复正文" in v1
        has_section_v3 = "回复正文" in v3
        print(f"     结构（有「回复正文」栏目）: v1={has_section_v1}, v3={has_section_v3}")

        has_note_v1 = "注意事项" in v1
        has_note_v3 = "注意事项" in v3
        print(f"     结构（有「注意事项」栏目）: v1={has_note_v1}, v3={has_note_v3}")

        # 语气检查
        polite_words = ["尊敬的", "您好", "抱歉", "感谢"]
        v1_polite = sum(1 for w in polite_words if w in v1)
        v3_polite = sum(1 for w in polite_words if w in v3)
        print(f"     语气（礼貌用语命中数）    : v1={v1_polite}, v3={v3_polite}")

        # 边界检查
        violations = ["全额退款", "承诺赔偿", "一定会赔"]
        v1_boundary = sum(1 for w in violations if w in v1)
        v3_boundary = sum(1 for w in violations if w in v3)
        print(f"     边界（越权词命中数）      : v1={v1_boundary}, v3={v3_boundary}")

        # 隐私检查
        privacy_leaks = ["13812345678", "sk-test-123456"]
        v1_leak = sum(1 for w in privacy_leaks if w in v1)
        v3_leak = sum(1 for w in privacy_leaks if w in v3)
        print(f"     隐私（敏感信息泄露数）    : v1={v1_leak}, v3={v3_leak}")

        print()


if __name__ == "__main__":
    main()
