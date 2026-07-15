## 云端模型验证（DeepSeek）

### 烟测结果
- 日期：2026-07-14
- 模型：deepseek-v4-flash
- 连通性：✅ 成功
- Prompt tokens：15
- Completion tokens：64
- Total tokens：79
- Prompt cache：0 hit / 15 miss
- 调用方式：PowerShell Invoke-RestMethod 直接调用 API

### 命令
```powershell
$env:DEEPSEEK_API_KEY="sk-xxx"
$headers = @{ "Authorization" = "Bearer $env:DEEPSEEK_API_KEY"; "Content-Type" = "application/json" }
$body = '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"只回复一句：DeepSeek v4-flash 已经可以调用。"}],"thinking":{"type":"disabled"},"max_tokens":64,"stream":false}'
Invoke-RestMethod -Uri "https://api.deepseek.com/chat/completions" -Method Post -Headers $headers -Body $body
```

### 方案说明
- 方案 A：DeepSeek 官方 API（低价模型 deepseek-v4-flash）
- 预算控制：max_tokens=64（烟测最小化成本）
- 后续正式调用 max_tokens 建议设 256-800

---

## 云端 Agent 验证

- Provider 名称：deepseek
- Base URL 类型：DeepSeek 官方 OpenAI 兼容接口 `https://api.deepseek.com`
- Agent 名称：exp4-deepseek
- 模型名或 Endpoint：deepseek-v4-flash
- 验证命令：
  - 模型级：`openclaw infer model run --local --model deepseek/deepseek-v4-flash --prompt "..." --json`
  - Agent 级：`openclaw agent --agent exp4-deepseek --local --message "..." --json`
- 返回是否成功：
  - 模型级：✅ 成功，返回 "OpenClaw DeepSeek v4-flash 低价路线已经跑通。"
  - Agent 级：✅ 成功，返回 "exp4-deepseek agent 已经跑通。"，耗时 19.4s，input 25667 tokens，output 12 tokens，finishReason=stop
- 日志中能看到的请求状态：
  - `[model-fetch] start provider=deepseek api=openai-completions model=deepseek-v4-flash method=POST url=https://api.deepseek.com/chat/completions`
  - `[model-fetch] response status=200 elapsedMs=257 contentType=text/event-stream`
- 密钥字段是否已用占位符表示：是，apiKey 存储在 `models.json`（真实值）和 `openclaw.json`（占位符/真实值）中，共享快照使用 `sk-xxx` 占位
- Agent 目录：`C:\Users\pc\.openclaw\agents\exp4-deepseek\agent`
- Workspace：`C:\Users\pc\.openclaw\workspace-exp4-deepseek`
- Session 文件：`C:\Users\pc\.openclaw\agents\exp4-deepseek\sessions\fbf9568f-3908-476b-92b4-14509f610390.jsonl`
