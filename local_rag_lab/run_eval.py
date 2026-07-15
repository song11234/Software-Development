import json
from pathlib import Path

from evaluators import evaluate_case
from samples import SAMPLES
from target_system import target_answer


def summarize(results: list[dict]) -> dict:
    total = len(results)
    passed = sum(1 for item in results if item["passed"])
    by_type = {}
    for item in results:
        stat = by_type.setdefault(item["category"], {"total": 0, "passed": 0})
        stat["total"] += 1
        stat["passed"] += int(item["passed"])
    return {
        "total": total,
        "passed": passed,
        "pass_rate": round(passed / total, 4) if total else 0,
        "by_type": by_type,
    }


def main() -> None:
    results = []
    for sample in SAMPLES:
        output = target_answer(sample["user_input"])
        results.append(evaluate_case(sample, output))

    report = {
        "summary": summarize(results),
        "results": results,
    }

    Path("outputs").mkdir(exist_ok=True)
    Path("outputs/eval_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()