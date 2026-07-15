"""提示词评估脚本 —— 验证整理提示词在不同输入上的表现。

对应知识点：第06章 提示词工程验证与评估。

用法（需要有效的 API Key）：
    python evals/test_prompts.py
"""
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.workflow import organize_document

# 评估用测试样本
EVAL_SAMPLES = [
    {
        "title": "React Hooks 使用技巧",
        "content": "React Hooks 是 React 16.8 引入的特性。useState 用于管理组件状态，useEffect 处理副作用。自定义 Hook 可以复用逻辑。",
        "expected_category": "技术/编程",
        "min_tags": 3,
    },
    {
        "title": "2024 年第一季度工作总结",
        "content": "本季度完成了产品 v2.0 发布，用户增长 30%，收入提升 25%。团队协作效率显著提高，下季度重点优化用户体验。",
        "expected_category": "工作/管理",
        "min_tags": 2,
    },
    {
        "title": "机器学习基础：决策树",
        "content": "决策树是一种监督学习算法，通过树形结构进行决策。每个内部节点代表一个特征测试，叶节点代表分类结果。常用的有 ID3、C4.5 和 CART 算法。",
        "expected_category": "学术/研究",
        "min_tags": 3,
    },
]


def evaluate():
    """运行评估并输出结果。"""
    print("提示词评估 — 资料整理")
    print("=" * 50)

    passed = 0
    failed = 0

    for i, sample in enumerate(EVAL_SAMPLES):
        print(f"\n样本 {i + 1}: {sample['title']}")
        try:
            result = organize_document(sample["title"], sample["content"])
            organized = result["result"]
            usage = result["token_usage"]

            # 检查分类
            category = organized.get("category", "")
            tags = organized.get("tags", [])
            summary = organized.get("summary", "")
            key_points = organized.get("key_points", [])

            checks = []
            # 检查标签数量
            if len(tags) >= sample["min_tags"]:
                checks.append(f"标签数 {len(tags)} >= {sample['min_tags']} OK")
            else:
                checks.append(f"标签数 {len(tags)} < {sample['min_tags']} FAIL")

            # 检查是否有摘要
            if summary and len(summary) >= 10:
                checks.append(f"摘要 OK ({len(summary)}字)")
            else:
                checks.append("摘要 FAIL")

            # 检查要点数量
            if len(key_points) >= 2:
                checks.append(f"要点 {len(key_points)} >= 2 OK")
            else:
                checks.append(f"要点 {len(key_points)} < 2 FAIL")

            print(f"  分类: {category}")
            print(f"  标签: {tags}")
            print(f"  摘要: {summary[:80]}...")
            print(f"  要点: {key_points[:3]}")
            print(f"  Token: {usage['total_tokens']}")

            all_ok = "FAIL" not in " ".join(checks)
            for c in checks:
                print(f"  {'✓' if 'OK' in c else '✗'} {c}")

            if all_ok:
                passed += 1
            else:
                failed += 1

        except Exception as e:
            print(f"  ✗ 错误: {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"评估结果: {passed} passed, {failed} failed ({len(EVAL_SAMPLES)} 样本)")

    return failed == 0


if __name__ == "__main__":
    # 检查 API Key
    from src.config import get_config

    try:
        config = get_config()
        success = evaluate()
        sys.exit(0 if success else 1)
    except ValueError as e:
        print(f"配置错误: {e}")
        print("提示词评估需要有效的 OPENAI_API_KEY。")
        sys.exit(1)
