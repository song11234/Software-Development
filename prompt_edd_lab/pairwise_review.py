"""
第十三阶段：成对比较与人工评审 (Pairwise Review)

比较两个提示词版本在相同样本上的输出，用统一维度记录评审结论。
核心思想：直接打绝对分困难时，比较 A vs B 哪个更好更容易。
"""

import json
from datetime import datetime
from prompt_versions import VERSIONS
from samples import SAMPLES
from target_system import target_answer

# ============================================================
# 比较维度
# ============================================================
PAIRWISE_CRITERIA = ["格式完整", "要点覆盖", "语气合适", "约束遵守", "安全稳健", "隐私保护"]


def build_pairwise_review(sample_id: str, output_a: str, output_b: str,
                          version_a: str = "A", version_b: str = "B") -> str:
    """生成成对比较模板，供人工评审使用。"""
    criteria_text = "\n".join(f"- {item}" for item in PAIRWISE_CRITERIA)
    return f"""样本：{sample_id}

请比较输出 {version_a} 和输出 {version_b}：

比较维度：
{criteria_text}

输出 {version_a}：
{output_a}

输出 {version_b}：
{output_b}

评审结论：
- 更好的输出：
- 主要原因：
- 仍需改进：
"""


# ============================================================
# 批量生成：用 target_system 模拟两个版本的输出做对比
# ============================================================
def generate_pairwise_batch(prompt_version_a: str, prompt_version_b: str) -> list[dict]:
    """
    用两个 prompt 版本生成同一组样本的输出，构造成对比较任务。
    
    真实场景：接入真实模型后，将 target_answer(user_input) 替换为
              model.generate(VERSIONS[ver](user_input))。
    """
    reviews = []
    for sample in SAMPLES:
        prompt_a = VERSIONS[prompt_version_a](sample["user_input"])
        prompt_b = VERSIONS[prompt_version_b](sample["user_input"])
        output_a = target_answer(sample["user_input"])
        output_b = target_answer(sample["user_input"])

        review_text = build_pairwise_review(
            sample["id"], output_a, output_b,
            version_a=prompt_version_a,
            version_b=prompt_version_b,
        )

        reviews.append({
            "sample_id": sample["id"],
            "category": sample["category"],
            "user_input": sample["user_input"],
            "version_a": prompt_version_a,
            "version_b": prompt_version_b,
            "output_a": output_a,
            "output_b": output_b,
            "review_template": review_text,
            # 人工评审填写区
            "winner": None,      # "A" / "B" / "平局"
            "reason": "",
            "improvement": "",
        })

    return reviews


# ============================================================
# 自测入口
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("PAIRWISE REVIEW GENERATOR")
    print("=" * 60)

    # 对比 v4_few_shot 和 v5_safety_privacy
    ver_a = "v4_few_shot"
    ver_b = "v5_safety_privacy"
    reviews = generate_pairwise_batch(ver_a, ver_b)

    # 打印每份评审表
    for r in reviews:
        print(f"\n{'─' * 60}")
        print(r["review_template"])

    # 保存完整数据
    timestamp = datetime.now().isoformat(timespec="seconds")
    report = {
        "generated_at": timestamp,
        "version_a": ver_a,
        "version_b": ver_b,
        "criteria": PAIRWISE_CRITERIA,
        "reviews": reviews,
    }

    output_path = "outputs/pairwise_reviews.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] 已生成 {len(reviews)} 份成对比较表 → {output_path}")
    print("请在评审结论区域填写：更好的输出 / 主要原因 / 仍需改进")
