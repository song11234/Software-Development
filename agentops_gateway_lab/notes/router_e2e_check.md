# Router 端到端验收

- 验收日期：2026-07-14 19:06
- Gateway 状态：✅ 运行中（pid 28136，127.0.0.1:18789）
- 飞书 WebSocket：✅ oc-deepseek + oc-qwen 均 running

| 测试消息 | 预期 Agent | 是否命中 | 是否回复 | 观察到的日志 | 备注 |
| --- | --- | --- | --- | --- | --- |
| @OC-DeepSeek-2410331105 /code Java 线程安全单例 | exp4-deepseek | ✅ | ✅ 输出 DCL 单例 + 场景 | CLI: provider=deepseek, model=v4-flash, stopReason=stop, 8.0s, 104 tokens | Agent 返回完整 Java 代码 |
| @OC-Qwen-2410331105 /chat RAG 外拒答 30 字 | exp4-qwen | ✅ | ✅ "资料外拒答防止 RAG 因知识缺失而编造错误答案，确保回答可靠性。" | CLI: provider=deepseek, model=v4-flash, stopReason=stop, 7.0s, 21 tokens | 精确 30 字 |
| 复合指令：规划+权限复核+配置复盘 | LLM Router → 多 Agent | ✅ | ✅ JSON 编排计划 | CLI: parallel mode, confidence=0.95, 4 agents, safety_gate=true | 详见 llm_router_check.md |
| LLM Router 低置信度案例 | LLM Router → 反问 | ✅ | ✅ JSON, confidence=0.3 | CLI: sequential mode, missing_info_policy=ask | 合格：信息不足时反问而非强行编排 |
| `/unknown` 前缀路由失败 | 应无匹配 / 帮助信息 | ⚠️ | ✅ 仍正常回复 | Gateway 日志显示：`dispatching to agent (session=agent:exp4-deepseek...)` | account binding 模式，不存在前缀匹配失败 |

## 对比观察

- 云端 Agent 响应特点（exp4-deepseek / DeepSeek v4-flash）：
  - 代码生成能力强，DCL 单例模式 + 适用场景一次到位
  - 响应速度：~8s（含工具上下文加载）
  - Token：721 in / 104 out，成本可控
  - 输出风格：完整、结构化、代码块+说明

- 本地/Qwen Agent 响应特点（exp4-qwen / DeepSeek v4-flash，非本地 Ollama）：
  - 简短精准，30 字约束严格遵守
  - 响应速度：~7s
  - Token：221 in / 21 out，非常精简
  - 输出风格：简洁直给

- LLM Router 输出 Agent 顺序（正常案例）：
  hermes-exp4-deepseek → exp4-deepseek → exp4-qwen → hermes-exp4-qwen
  汇总人：hermes-exp4-deepseek

- LLM Router 输出 Agent 顺序（低置信度案例）：
  exp4-deepseek → exp4-qwen → hermes-exp4-deepseek → hermes-exp4-qwen
  confidence=0.3，policy=ask，应反问而非执行

- LLM Router 是否需要人工确认：
  - 高置信度（0.95）：safety_gate=true 仍建议复核
  - 低置信度（0.3）：必须反问，不能自动编排

- 路由误配或未命中的表现：
  - 当前 account binding 模式不存在前缀匹配失败问题
  - 两个 account 分别绑定不同 Agent，@错机器人最多走到错误的角色

- 飞书实测状态：
  - ⚠️ CLI 端 Agent E2E 已全部通过（Provider→Agent→Model 链路完整）
  - ⚠️ 飞书测试群实际 @消息测试：**需用户在飞书中手动发送消息确认**（无法从 CLI 获取 chat_id 发群消息）
  - Phase 4 已验证飞书 WebSocket 双向通信正常

## 需要改进的地方

- [ ] `groupPolicy: "open"` + `allowFrom: ["*"]` 需收紧为 allowlist
- [ ] 飞书应用 scope 未开通完整权限（`im:message`、`im:message.reactions:write_only`、`contact:contact.base:readonly` 等），导致 card/streaming 400 错误，需补齐
- [ ] 路由机制需明确：当前为 account binding，不是 `/code`、`/chat` 前缀路由；文档中前缀失败案例在此模式下不会触发
- [ ] 飞书群内直接 @测试四个机器人端到端（当前仅 CLI 验证）
- [ ] 日志中 `lastInboundAt: null` 的问题，实际 Gateway 已能接收 inbound（见 logs/error_cases.log），需更新状态
- [ ] `plugins.allow` 为空但 feishu/codex 已加载，建议显式声明允许列表
- [ ] main Agent 报 `No API key found for provider "openai"`，虽不影响实验 Agent，但需清理

## 验证命令汇总

```bash
# Agent E2E 验证
openclaw agent --agent exp4-deepseek --local --thinking off \
  --message '/no_think ...Java 线程安全单例...' --json
openclaw agent --agent exp4-qwen --local --thinking off \
  --message '/no_think ...RAG 外拒答...' --json

# LLM Router 正常 + 失败案例
openclaw infer model run --local --model deepseek/deepseek-v4-flash \
  --prompt '...复合指令...' --json
openclaw infer model run --local --model deepseek/deepseek-v4-flash \
  --prompt '...信息不足的模糊指令...' --json

# Router 绑定确认
openclaw agents bindings --json
openclaw channels status --json
```
