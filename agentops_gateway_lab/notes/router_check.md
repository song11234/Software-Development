# Router 配置验证

## 路由方式

当前 OpenClaw 2026.6.11 不支持前缀路由命令 (`openclaw configure router add --prefix`)，采用 **account binding** 方式实现等效分流。

## 当前绑定关系

```
飞书测试群
├── @OC-DeepSeek-2410331105 (AppId ...dbc9)
│   └── oc-deepseek account → exp4-deepseek Agent → exp4-code-review Skill
│
└── @OC-Qwen-2410331105 (AppId ...5bed)
    └── oc-qwen account → exp4-qwen Agent → exp4-local-explain Skill
```

## 验证命令

```
openclaw agents bindings --json
```

## 输出结果

```json
[
  {
    "agentId": "exp4-deepseek",
    "match": {
      "channel": "feishu",
      "accountId": "oc-deepseek"
    },
    "description": "feishu accountId=oc-deepseek"
  },
  {
    "agentId": "exp4-qwen",
    "match": {
      "channel": "feishu",
      "accountId": "oc-qwen"
    },
    "description": "feishu accountId=oc-qwen"
  }
]
```

## 路由模式说明

- 采用 **不同机器人 → 不同 account → 不同 Agent** 的绑定方式
- 当前版本不支持同一 Channel 的前缀路由（如 `/code` → exp4-deepseek、`/chat` → exp4-qwen）
- 用户在飞书群内 @不同的机器人 即可将消息路由到不同 Agent
- 两个 Agent 当前均使用 `deepseek/deepseek-v4-flash` 模型（非本地 Ollama）
- Agent 角色通过 workspace 中的 SKILL.md 和 IDENTITY.md 区分

## 规则 Router 能解决的问题

- 确定性分流：根据 account 来源将请求精确分发到预定 Agent
- 角色隔离：不同机器人承担不同职责（代码审查 vs 课堂解释）
- 稳定的验收路径：测试时知道哪个机器人会回复什么风格的内容

## 待改进

- [ ] 当前 `groupPolicy: "open"` + `allowFrom: ["*"]`，安全风险较高，应改为 allowlist
- [ ] Hermes 的 DeepSeek 和 Qwen 飞书应用尚未创建（阶段七）
- [ ] 缺少 LLM Router 层面的动态编排能力（当前仅规则路由）
