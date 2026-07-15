## 本地/第二 Agent 验证

> 注：本阶段 exp4-qwen 实际使用 DeepSeek v4-flash（非本地 Ollama），两个 Agent 使用同一 Provider 但不同角色和 Skill。

- Ollama 版本：**未使用**（本阶段用 DeepSeek 替代）
- 本地模型名称：N/A
- Provider 名称：`deepseek`（复用）
- `exp4-deepseek` Agent：
  - 模型：`deepseek/deepseek-v4-flash`
  - Skill：`exp4-code-review`（代码审查员）
  - 飞书机器人：OC-DeepSeek-2410331105
  - CLI 验证：✅ 通过，`stopReason=stop`，返回正确
- `exp4-qwen` Agent：
  - 模型：`deepseek/deepseek-v4-flash`
  - Skill：`exp4-local-explain`（课堂答疑助手）
  - 飞书机器人：OC-Qwen-2410331105
  - CLI 验证：⚠️ API 调用成功（status=200），但返回文本为空（`NO_REPLY`），需飞书端实际验证
- 验证命令：
  ```
  openclaw agent --agent exp4-deepseek --local --message "..." --json
  openclaw agent --agent exp4-qwen --local --message "..." --json
  ```
- 是否断网测试：否（使用云端模型）
- 两个 Agent 角色区分：✅ exp4-deepseek（代码审查）与 exp4-qwen（答疑解释）使用不同 Skill

### 文件布局

```
~/.openclaw/workspace-exp4-deepseek/
├── AGENTS.md
├── IDENTITY.md
└── skills/exp4-code-review/SKILL.md

~/.openclaw/workspace-exp4-qwen/
├── AGENTS.md
├── IDENTITY.md
└── skills/exp4-local-explain/SKILL.md
```

### Binding 配置

| 飞书机器人 | Channel Account | Agent | Skill |
|-----------|----------------|-------|-------|
| OC-DeepSeek-2410331105 | oc-deepseek | exp4-deepseek | exp4-code-review |
| OC-Qwen-2410331105 | oc-qwen | exp4-qwen | exp4-local-explain |
