## 飞书 Channel 验证

- `OC-DeepSeek-2410331105` 应用名称与 App ID 后四位：`OC-DeepSeek-2410331105`，App ID: `cli_aadf64ad813a`**dbc9**
- `OC-Qwen-2410331105` 应用名称与 App ID 后四位：`OC-Qwen-2410331105`，App ID: `cli_aadf5d4ea8b`**5bed**
- `Hermes-DeepSeek-2410331105` 应用名称与 App ID 后四位：**尚未创建**（待阶段七 Hermes 配置）
- `Hermes-Qwen-2410331105` 应用名称与 App ID 后四位：**尚未创建**（待阶段七 Hermes 配置）
- OpenClaw Channel 名称：`feishu`
- Hermes Gateway 名称或状态：**尚未接入飞书**（待阶段七在 WSL2 中配置）
- 连接模式：**WebSocket**（飞书长连接 / 无需公网回调 URL）
- 已申请权限：
  - `im:message:send_as_bot` — 以机器人身份发送消息
  - `im:message.p2p_msg:readonly` — 读取发给机器人的私聊消息
  - `im:message.group_at_msg:readonly` — 接收群内 @ 机器人的消息
  - `im:chat:read` — 读取群聊信息（测试阶段使用，后续需评估是否降权）
- 运行时仍缺少的权限（日志中出现 `code: 99991672`）：
  - `im:message` / `im:message.reactions:write_only` — 导致流式卡片/streaming 创建 400，已 fallback 到非流式卡片
  - `contact:contact.base:readonly` / `contact:contact:access_as_app` / `contact:contact:readonly` / `contact:contact:readonly_as_app` — 飞书联系信息读取权限
  - 影响：不影响文本消息到达，但会导致部分卡片/streaming 功能失败，建议后续补齐
- 是否完成版本发布：✅ 是（两个应用均已发布，机器人可在飞书中正常收发消息）
- 测试群 `chat_id` 来源：Gateway 日志 — `oc_1c575365d2ed132d9c6bf17603e5d19e`（从 `/unknown` 测试消息事件日志中提取）
- 测试用户 `open_id`：Gateway 日志 — `ou_09f0c7fad2307209b61eb161af534a53`
- OpenClaw 测试群 `groups` 是否设置 `requireMention` 与群内 `allowFrom`：`requireMention: true`（群内 @ 才触发），`groupPolicy: "open"`（测试阶段），`allowFrom: ["*"]`
- OpenClaw 如出现 `not in groupAllowFrom`，测试群 `chat_id` 是否也已写入 `groupAllowFrom`：未设置 `groupAllowFrom`，因为当前使用 `groupPolicy: "open"`
- `Hermes-DeepSeek-2410331105` pairing 是否已批准或写入 `FEISHU_ALLOWED_USERS`：**N/A**（尚未创建）
- `Hermes-Qwen-2410331105` pairing 是否已批准或写入 `FEISHU_ALLOWED_USERS`：**N/A**（尚未创建）
- Hermes 是否设置 `FEISHU_GROUP_POLICY=disabled` 或等价 `default_group_policy: disabled`：**N/A**（尚未配置）
- 测试群外是否默认不响应：当前 `groupPolicy: "open"` + `allowFrom: ["*"]`，**测试阶段未限制群外响应**，后续阶段需收紧为 allowlist
- OpenClaw 测试消息是否抵达网关：✅ 是（OC-DeepSeek 和 OC-Qwen 均可在群聊中正常回复）
- Hermes 测试消息是否抵达 Gateway：**N/A**（尚未配置）
- 日志中的连接状态：
  - OC-DeepSeek：`running: true`，WebSocket 长连接正常，lastInboundAt 有记录
  - OC-Qwen：`running: true`，WebSocket 长连接正常（首次启动有 reconnect，重连后恢复）
- 是否使用四个机器人：❌ 当前仅 2 个（OC-DeepSeek、OC-Qwen），Hermes-DeepSeek 和 Hermes-Qwen 待阶段七创建
- 敏感字段来源与占位符处理说明：
  - App ID / App Secret：来自飞书开放平台「凭证与基础信息」页，只写入本机 `~\.openclaw\openclaw.json`
  - API Key：来自 DeepSeek 控制台 API Keys 页面，只写入本机配置文件
  - 共享文档（本文档）中不包含任何真实凭证

---

### 验证过程记录

1. **飞书后台配置**：在 `open.feishu.cn` 创建两个企业自建应用 `OC-DeepSeek-2410331105` 和 `OC-Qwen-2410331105`，添加机器人能力，订阅 `im.message.receive_v1`，配置权限并发布版本。

2. **OpenClaw 配置**：通过 `openclaw channels add --channel feishu` 分别添加两个 account（`oc-deepseek`、`oc-qwen`），写入 `openclaw.json`。

3. **首次调试问题**：
   - 初始 `channels: {}` 为空 → 飞书 plugin 未安装，通过 `openclaw channels add` 解决
   - OC-Qwen 首次 @ 无回复 → 日志分析显示 WebSocket 已连接但出现一次 reconnect，重连后恢复正常

4. **端到端验证**：在飞书测试群中分别 @OC-DeepSeek-2410331105 和 @OC-Qwen-2410331105，两者均能正常回复。
5. **路由机制验证（`/unknown` 测试）**：发送 `@OC-DeepSeek-2410331105 /unknown 请解释单元测试是什么`，机器人仍然正常回复。日志显示 Gateway 直接将消息 dispatch 给 `exp4-deepseek`，未做前缀匹配。结论：当前路由模式为 **account binding**，不是文档中描述的 `/code` / `/chat` 前缀路由。此发现已记录到 `logs/error_cases.md` 与 `router_e2e_check.md`。
6. **权限缺口**：日志中出现 `im:message`、`contact:contact.base:readonly` 等 scope 缺失的 `99991672` 错误，但文本消息仍能正常到达与回复。


### 当前配置摘要

| 机器人 | 飞书 App ID (后四位) | 框架 Agent | 模型 | 连接方式 |
|--------|---------------------|-----------|------|---------|
| OC-DeepSeek-2410331105 | ...dbc9 | exp4-deepseek | deepseek-v4-flash | WebSocket |
| OC-Qwen-2410331105 | ...5bed | exp4-qwen | deepseek-v4-flash | WebSocket |

> **阶段五完成**：OC-Qwen 已绑定独立 Agent `exp4-qwen`，使用 deepseek-v4-flash（非本地 Ollama）。两个 Agent 角色区分：exp4-deepseek→exp4-code-review，exp4-qwen→exp4-local-explain。

### 待改进项

- [ ] `groupPolicy` 和 `allowFrom` 当前为 `open` / `["*"]`，测试完成需改为 allowlist
- [ ] 补齐飞书应用权限：`im:message`、`im:message.reactions:write_only`、`contact:contact.base:readonly` 等（日志中有 `99991672` 错误）
- [x] OC-Qwen 需绑定独立 Agent `exp4-qwen`（阶段五 ✅）
- [x] 阶段六 Router 配置 + LLM Router 观察（阶段六 ✅）
- [x] 飞书端到端验收（阶段六 ✅，详见 `router_e2e_check.md`）
- [x] `/unknown` 前缀路由测试完成（机器人正常回复，说明是 account binding 模式，已记录）
- [x] 记录测试群 `chat_id` 和用户 `open_id`（`oc_1c575365d2ed132d9c6bf17603e5d19e`，`ou_09f0c7fad2307209b61eb161af534a53`）
- [ ] 创建 Hermes-DeepSeek 和 Hermes-Qwen 飞书应用（阶段七）
