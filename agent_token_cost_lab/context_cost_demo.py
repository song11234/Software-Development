import asyncio
import json
from dataclasses import asdict

from cost_runtime import CostPolicy, LlmRequest, run_requests


QUESTION = "请给出三条降低大模型 Token 成本的工程建议。"

LONG_HISTORY = "\n".join(
    [
        f"第{i}轮历史：我们讨论了一个与当前问题关系不大的实现细节，包括日志格式、按钮颜色和临时命令。"
        for i in range(1, 21)
    ]
)

SUMMARY_HISTORY = "历史摘要：前面讨论过日志、预算和输出长度；当前只需要回答 Token 成本控制建议。"


def system_message() -> dict:
    return {
        "role": "system",
        "content": "关闭 thinking，只输出最终答案。回答不超过 120 个中文字。",
    }


async def main() -> None:
    policy = CostPolicy(
        max_concurrency=1,
        request_timeout=60,
        retries=1,
        max_prompt_tokens=1800,
        run_token_budget=2600,
        max_output_tokens=120,
    )
    requests = [
        LlmRequest(
            request_id="context-short",
            scenario="short_context",
            messages=[system_message(), {"role": "user", "content": QUESTION}],
        ),
        LlmRequest(
            request_id="context-long",
            scenario="long_history_context",
            messages=[
                system_message(),
                {"role": "user", "content": f"{LONG_HISTORY}\n\n当前问题：{QUESTION}"},
            ],
        ),
        LlmRequest(
            request_id="context-summary",
            scenario="summary_context",
            messages=[
                system_message(),
                {"role": "user", "content": f"{SUMMARY_HISTORY}\n\n当前问题：{QUESTION}"},
            ],
        ),
    ]

    results = await run_requests(requests, policy, log_path="logs/context_cost.jsonl")
    for result in results:
        printable = asdict(result)
        printable["answer"] = result.answer[:80].replace("\n", " ")
        print(json.dumps(printable, ensure_ascii=False))

    print("log_path: logs/context_cost.jsonl")


if __name__ == "__main__":
    asyncio.run(main())
