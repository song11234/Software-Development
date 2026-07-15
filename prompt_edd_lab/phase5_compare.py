"""
第五阶段：基线提示词 vs 改进提示词对比

对全部 6 条样本，分别用 v1_baseline 和 v3_format_rules 调用 DeepSeek，
然后用 rubric 评分系统逐条打分，输出对比报告。
"""

from config import get_llm_response
from samples import SAMPLES
from rubric import score_output, print_report, print_summary
from prompt_versions import VERSIONS, VERSION_INFO


def run_experiment(version_id: str, samples):
    """对指定版本跑全部样本，返回 (outputs, results)"""
    prompt_fn = VERSIONS[version_id]
    outputs = []
    for i, sample in enumerate(samples):
        print(f"  [{i+1}/{len(samples)}] {sample['id']} ({sample['category']}) ... ", end="", flush=True)
        prompt = prompt_fn(sample["user_input"])
        output = get_llm_response(prompt)
        if output is None:
            output = "[ERROR] Model returned no response"
        outputs.append(output)
        print(f"{len(output)} chars")
    return outputs


def main():
    versions_to_test = ["v1_baseline", "v3_format_rules"]

    print("=" * 60)
    print("PHASE 5: BASELINE vs IMPROVED PROMPT COMPARISON")
    print("=" * 60)

    all_outputs = {}

    for vid in versions_to_test:
        info = next(v for v in VERSION_INFO if v["id"] == vid)
        print(f"\n>>> Running: {vid}")
        print(f"    Description: {info['change']} -> {info['expected_benefit']}")
        outputs = run_experiment(vid, SAMPLES)
        all_outputs[vid] = outputs

    # ---- 两版本分别评分 ----
    print("\n\n" + "=" * 60)
    print("SCORING RESULTS")
    print("=" * 60)

    for vid in versions_to_test:
        results = [score_output(s, o) for s, o in zip(SAMPLES, all_outputs[vid])]
        print(f"\n{'#' * 60}")
        print(f"# {vid}")
        print(f"{'#' * 60}")
        for r in results:
            print_report(r)
        print_summary(results)

    # ---- 逐样本对比 ----
    print("\n\n" + "=" * 60)
    print("HEAD-TO-HEAD COMPARISON (per sample)")
    print("=" * 60)

    v1_results = [score_output(s, o) for s, o in zip(SAMPLES, all_outputs["v1_baseline"])]
    v3_results = [score_output(s, o) for s, o in zip(SAMPLES, all_outputs["v3_format_rules"])]

    total_diff = 0
    for i, sample in enumerate(SAMPLES):
        v1_total = v1_results[i]["total"]
        v3_total = v3_results[i]["total"]
        diff = v3_total - v1_total
        total_diff += diff
        better = "v3" if diff > 0 else ("v1" if diff < 0 else "tie")
        print(f"\n  {sample['id']} ({sample['category']})")
        print(f"    v1: {v1_total}/12  |  v3: {v3_total}/12  |  diff: {diff:+d}  [{better}]")
        # 按维度展示谁更强
        dim_changes = []
        for dim in ["format", "coverage", "constraint", "tone", "safety", "privacy"]:
            d = v3_results[i]["scores"][dim] - v1_results[i]["scores"][dim]
            if d != 0:
                dim_changes.append(f"{dim}: {d:+d}")
        if dim_changes:
            print(f"    dimension changes: {', '.join(dim_changes)}")

    print(f"\n\nOverall v3 improvement: {total_diff:+d} points across {len(SAMPLES)} samples")

    # ---- 按分类汇总 v1 vs v3 维度平均分 ----
    print(f"\n{'=' * 60}")
    print("DIMENSION BREAKDOWN: v1 vs v3")
    print(f"{'=' * 60}")
    print(f"{'Dimension':<14} {'v1_avg':>7} {'v3_avg':>7} {'delta':>7}")
    print("-" * 40)
    for dim in ["format", "coverage", "constraint", "tone", "safety", "privacy"]:
        v1_avg = sum(r["scores"][dim] for r in v1_results) / len(v1_results)
        v3_avg = sum(r["scores"][dim] for r in v3_results) / len(v3_results)
        print(f"  {dim:<14} {v1_avg:>6.1f} {v3_avg:>6.1f} {v3_avg - v1_avg:>+7.1f}")

    # 总览
    v1_overall = sum(r["total"] for r in v1_results)
    v3_overall = sum(r["total"] for r in v3_results)
    print("-" * 40)
    print(f"  {'OVERALL':<14} {v1_overall/6:>6.1f} {v3_overall/6:>6.1f} {(v3_overall-v1_overall)/6:>+7.1f}")


if __name__ == "__main__":
    main()
