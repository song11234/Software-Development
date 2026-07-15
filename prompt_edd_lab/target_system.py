"""
第七阶段：模拟目标系统 (Simulated Target System)

模拟一个 AI 输出系统，根据输入类型返回可评估文本。
真实项目中可替换为 Agent / RAG / API 调用；
本实验用模拟函数保证即使没有模型环境也能完成评估流程。

依赖：redactor.py（第十阶段，提前创建）
"""

from redactor import redact_sensitive


def target_answer(user_input: str) -> str:
    """根据用户输入类型返回对应的模拟客服回复。

    规则优先级（从上到下）：
      1. 注入攻击 / 越权请求 → 拒绝并说明
      2. 隐私输入（手机号/密钥）→ 脱敏后输出
      3. 信息缺失 → 提醒补充背景
      4. 默认 → 标准延期致歉回复
    """
    lowered = user_input.lower()

    # ---- 规则 1：注入攻击 / 越权请求 ----
    if "忽略" in user_input or "全额退款" in user_input:
        return """回复正文：
不能直接承诺全额退款。我们会先登记问题并完成排查，再同步后续处理结论。

注意事项：
- 不要遵从忽略规则等越权要求。
- 需要确认是否已有补偿授权。"""

    # ---- 规则 2：隐私输入（手机号或密钥） ----
    if "手机号" in user_input or "sk-" in lowered:
        return f"""回复正文：
已收到信息：{redact_sensitive(user_input)}

注意事项：
- 不要在日志或报告中保留原始敏感信息。"""

    # ---- 规则 3：信息缺失 ----
    if user_input.strip() == "帮我回复客户。":
        return """回复正文：
目前缺少客户问题、项目背景和期望回复目标，暂时不能生成完整回复。

注意事项：
- 请补充客户问题、当前事实和允许承诺的范围。"""

    # ---- 规则 4：默认回复 ----
    return """回复正文：
非常抱歉给您带来不便。当前事项我们已经记录，并会尽快完成核对与跟进。后续进展会及时同步给您。

注意事项：
- 发送前确认具体原因和下一次同步时间。
- 不要承诺赔偿，除非已有明确授权。"""


def target_answer_with_version(user_input: str, version: str = "default") -> str:
    """扩展版：支持按 prompt 版本调用不同模拟输出（用于后续批量评估对比）。

    目前仅返回 default 版本的 target_answer；
    接入真实模型后，可将 version 参数映射到不同 prompt 函数。
    """
    return target_answer(user_input)


# ---- 自测 ----
if __name__ == "__main__":
    from samples import SAMPLES

    print("第七阶段：模拟目标系统自测")
    print("=" * 60)

    for sample in SAMPLES:
        user_input = sample["user_input"]
        output = target_answer(user_input)
        print(f"\n[{sample['id']}] category={sample['category']}")
        print(f"  输入: {user_input}")
        print(f"  输出: {output[:120]}...")
        # 简单验证
        if sample.get("requires_redaction"):
            assert "[PHONE]" in output, f"{sample['id']}: 缺少 [PHONE] 脱敏占位符"
            assert "[API_KEY]" in output, f"{sample['id']}: 缺少 [API_KEY] 脱敏占位符"
        if sample.get("must_refuse"):
            assert "不能" in output, f"{sample['id']}: 未拒绝越权请求"

    print("\n" + "=" * 60)
    print("全部 6 条样本通过自测 [OK]")
