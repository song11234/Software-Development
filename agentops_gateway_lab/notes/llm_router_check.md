# LLM Router 编排观察

## 测试 1：飞书四机器人接入流程规划

- 原始用户指令：请规划飞书四机器人接入流程，检查权限风险，并给出 OpenClaw 配置复盘清单
- 使用的 Router：OpenClaw 模型级推理 (`openclaw infer model run --model deepseek/deepseek-v4-flash`)
- Router 输出是否为结构化 JSON：✅ 是
- `intent`：飞书机器人接入流程规划与权限风险检查及配置复盘
- `execution_mode`：`parallel`（并行编排）
- `confidence`：0.8
- 被选择的 Agent 顺序：
  1. exp4-deepseek
  2. exp4-qwen
  3. hermes-exp4-deepseek
- `final_responder`：`hermes-exp4-qwen`
- `safety_gate`：`true`（包含安全复核）
- 低置信度时是否要求反问：confidence 0.8 处于中高水平，但未显式触发反问策略

## 测试 2：实验4作业初筛与风险检查助手

- 原始用户指令：授课老师要求四个智能体协作检查一份实验4提交材料是否包含 OpenClaw/Hermes 双 gateway、四个飞书机器人、DeepSeek 与本地 Qwen、qwen no-thinking、Router/LLM Router 证据、权限与脱敏证据，并生成实验4作业初筛报告
- 使用的 Router：OpenClaw 模型级推理 (`openclaw infer model run --model deepseek/deepseek-v4-flash`)
- Router 输出是否为结构化 JSON：✅ 是
- `intent`：检查实验4提交材料是否包含所需证据，并生成初筛报告
- `execution_mode`：`parallel`
- `confidence`：0.95（高置信度）
- 被选择的 Agent 顺序：
  1. hermes-exp4-deepseek
  2. exp4-deepseek
  3. exp4-qwen
  4. hermes-exp4-qwen
- `final_responder`：`hermes-exp4-deepseek`（项目经理汇总）
- `safety_gate`：`true`
- `missing_info_policy`：`ask`（缺信息时反问）
- 是否包含安全复核：是

## 编排回放验证

### 步骤 1：exp4-deepseek（OpenClaw 深代码审查员）
- 实际调用方式：`openclaw agent --agent exp4-deepseek --local --thinking off`
- 输出摘要：生成完整检查清单，包含 5 项通过、4 项风险（权限过宽/密钥硬编码/超时缺失/重试缺失）、6 项建议补证
- 是否需要修正：否

### 步骤 2：exp4-qwen（OpenClaw 本地说明员）
- 实际调用方式：`openclaw agent --agent exp4-qwen --local --thinking off`
- 输出摘要：返回确认消息，回复较短（14 output tokens），支持飞书实际 @ 场景下的正常交互
- 是否需要修正：否（CLI 测试通过）

### 步骤 3 & 4：hermes-exp4-deepseek & hermes-exp4-qwen
- 状态：⚠️ 暂未配置（Hermes 飞书应用未创建，待阶段七完成）
- 计划在阶段七创建 Hermes-DeepSeek 和 Hermes-Qwen 飞书机器人后补充

## 反思

### 规则 Router 能解决的问题
- 确定性分流：用户 @哪个机器人 → 明确哪个 Agent 回复
- 角色固定：每个机器人有明确的 Skill 和身份
- 低延迟：rule-based 匹配无额外 LLM 调用开销
- 可预测性强：测试验证路径稳定

### LLM Router 比规则 Router 更适合的问题
- 复合自然语言指令需要拆解为多步骤任务
- 需要动态判断哪个 Agent 最适合当前问题
- 用户没有明确指定 Agent 时自动编排
- 多 Agent 协作场景下任务分发与汇总

## 测试 3：LLM Router 低置信度 / 失败案例

- 原始用户指令：请处理一下那个配置，顺便看一下安全问题。
- Router 输出：

```json
{
  "intent": "configuration_processing_and_security_review",
  "execution_mode": "sequential",
  "agents": ["exp4-deepseek", "exp4-qwen", "hermes-exp4-deepseek", "hermes-exp4-qwen"],
  "final_responder": "exp4-deepseek",
  "safety_gate": true,
  "confidence": 0.3,
  "missing_info_policy": "ask"
}
```

- 分析：用户指令「那个配置」「安全问题」极度模糊——没说是哪个平台、哪个框架、期望什么输出。LLM Router 正确地将 confidence 降至 **0.3**，并设置 `missing_info_policy: "ask"`（反问），**不应该**直接调用四个 Agent。合格。

### LLM Router 可能误判的地方
- 短问题可能被过度分解导致不必要的多 Agent 调用
- 模型幻觉可能导致选择不存在的 Agent
- 上下文不足时 confidence 估计可能不准
- safety_gate 判断可能因 prompt 措辞不同而波动

### 如果 Router 置信度低，系统应该如何 fail closed
- confidence < 0.5 时应反问用户确认意图
- 涉及高风险操作（密钥、权限变更）应强制进入人工确认
- 不能自动降级到默认 Agent 执行未确认的高风险任务
- 应记录低置信度路由决策的完整上下文日志
