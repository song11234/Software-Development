from real_llm_client import chat_completion, estimate_cost


def main() -> None:
    messages = [
        {
            "role": "system",
            "content": "关闭 thinking，只输出最终答案。回答不超过 80 个中文字。",
        },
        {
            "role": "user",
            "content": "用两句话说明为什么长上下文会增加大模型调用成本。",
        },
    ]

    response = chat_completion(messages)
    print("model:", response.model)
    print("content:", response.content.strip())
    print("prompt_tokens:", response.usage.prompt_tokens)
    print("completion_tokens:", response.usage.completion_tokens)
    print("total_tokens:", response.usage.total_tokens)
    print("usage_estimated:", response.usage.estimated)
    print("estimated_cost:", estimate_cost(response.usage.prompt_tokens, response.usage.completion_tokens))
    print("elapsed_ms:", response.elapsed_ms)


if __name__ == "__main__":
    main()
