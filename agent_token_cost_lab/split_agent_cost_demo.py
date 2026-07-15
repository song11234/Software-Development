import asyncio
import json
from dataclasses import asdict

from cost_runtime import CostAwareController, CostPolicy, LlmRequest


BACKGROUND = "\n".join(
    [
        "课程背景：同学们主要依靠实验文档、AI 工具排障和授课老师答疑完成实验。",
        "实验约束：真实模型必须使用小模型或低成本 API，不能默认要求大模型。",
        "工程要求：日志不能记录 API Key、完整 prompt 或内部服务地址。",
        "运行时要求：并发数从 1 或 2 开始，失败重试不超过 1 到 2 次。",
        "无关信息：这里还有一段关于界面配色、文件命名和课堂座位安排的讨论，对当前任务帮助很小。",
    ]
    * 5
)

TASK = "为第08章实验写一段 Token 成本控制建议，要求适合普通学生笔记本。"


def system_message() -> dict:
    return {
        "role": "system",
        "content": "关闭 thinking，只输出最终答案。回答保持简短、具体。",
    }


async def main() -> None:
    policy = CostPolicy(
        max_concurrency=1,
        request_timeout=60,
        retries=1,
        max_prompt_tokens=2200,
        run_token_budget=4200,
        max_output_tokens=120,
    )
    controller = CostAwareController(policy, log_path="logs/split_agent_cost.jsonl")

    monolithic = await controller.handle(
        LlmRequest(
            request_id="single-agent",
            scenario="single_agent_full_context",
            messages=[
                system_message(),
                {"role": "user", "content": f"背景资料：\n{BACKGROUND}\n\n任务：{TASK}"},
            ],
        )
    )

    planner = await controller.handle(
        LlmRequest(
            request_id="planner",
            scenario="split_planner_task_only",
            messages=[
                system_message(),
                {"role": "user", "content": f"只根据任务写一个三步计划，不要展开背景。\n任务：{TASK}"},
            ],
        )
    )

    worker = await controller.handle(
        LlmRequest(
            request_id="worker",
            scenario="split_worker_extract_facts",
            messages=[
                system_message(),
                {
                    "role": "user",
                    "content": f"从背景中提取与 Token 成本控制直接相关的 5 条事实。\n背景：\n{BACKGROUND}",
                },
            ],
        )
    )

    summarizer = await controller.handle(
        LlmRequest(
            request_id="summarizer",
            scenario="split_summarizer_small_context",
            messages=[
                system_message(),
                {
                    "role": "user",
                    "content": (
                        f"任务：{TASK}\n"
                        f"计划：{planner.answer}\n"
                        f"相关事实摘要：{worker.answer}\n"
                        "请给出最终建议。"
                    ),
                },
            ],
        )
    )

    results = [monolithic, planner, worker, summarizer]
    for result in results:
        printable = asdict(result)
        printable["answer"] = result.answer[:80].replace("\n", " ")
        print(json.dumps(printable, ensure_ascii=False))

    split_total = sum(item.total_tokens for item in [planner, worker, summarizer])
    print("=" * 80)
    print("single_agent_total_tokens:", monolithic.total_tokens)
    print("split_agents_total_tokens:", split_total)
    print("note: 拆分是否省 Token 取决于是否减少重复上下文，而不是取决于 Agent 数量。")
    print("log_path: logs/split_agent_cost.jsonl")


if __name__ == "__main__":
    asyncio.run(main())
