## 环境验证记录

### OpenClaw（Windows）
- 版本：OpenClaw 2026.6.11 (e085fa1)
- 安装方式：Windows Native（npm/pnpm）
- `openclaw doctor` 结果：✅ 通过，非 git 安装
- Gateway 状态：未启动，配置文件 `~\.openclaw\openclaw.json` 缺失
- Gateway 端口：loopback 127.0.0.1:18789
- 配置路径：`~\.openclaw\`
- 日志路径：`~\AppData\Local\Temp\openclaw\openclaw-2026-07-13.log`

### Hermes Agent（WSL2 Ubuntu）
- 版本：Hermes Agent v0.18.2 (2026.7.7.2)
- 安装方式：WSL2，git 安装
- `hermes doctor` 结果：✅ 通过
- 模型 Provider：DeepSeek（API 已连通）
- CLI 对话测试：✅ 成功
- 配置路径：`~/.hermes/`
- Python：3.11.15

### 架构说明
```
Windows（本机）                    WSL2 Ubuntu
─────────────                      ────────────
OpenClaw 2026.6.11                 Hermes v0.18.2
├── Gateway: 127.0.0.1:18789       ├── DeepSeek Provider ✅
├── Config: ~\.openclaw\           ├── Config: ~/.hermes/
└── 状态: 未启动                    └── CLI 对话: 通过
```

### 遇到的问题
- Windows 原生不支持 `hermes` 命令，需在 WSL2 中使用
- OpenClaw Gateway 尚未启动，配置文件缺失（后续阶段创建）

---

## 本章系统图

- Channel：飞书（待接入），四个企业自建应用：`OC-DeepSeek-<STUDENT_ID>`、`OC-Qwen-<STUDENT_ID>`、`Hermes-DeepSeek-<STUDENT_ID>`、`Hermes-Qwen-<STUDENT_ID>`
- Router：OpenClaw 前缀路由 `/code` `/chat` 或 account binding（待配置）
- LLM Router：Hermes 语义路由，`hermes-exp4-deepseek` 作为任务规划与最终汇总者（待配置）
- Cloud Agent：`exp4-deepseek`（OpenClaw） + `hermes-exp4-deepseek`（Hermes），均接入 DeepSeek v4-flash
- Local Agent：`exp4-qwen`（OpenClaw） + `hermes-exp4-qwen`（Hermes），均接入本地 Ollama qwen3.6
- Provider：云端 DeepSeek API（已连通） + 本地 Ollama（待配置）
- OpenClaw 配置文件路径：`~\.openclaw\openclaw.json`（Windows）
- Hermes 配置目录：`~/.hermes/`（WSL2），含 `config.yaml`、`.env`、`sessions/`、`logs/`、`skills/`
- 日志观察位置：OpenClaw → `%TEMP%\openclaw\`；Hermes → `~/.hermes/logs/`

```text
用户消息（飞书）──────────────────────────────────────────┐
                                                          │
  Windows 本机                    WSL2 Ubuntu              │
  ────────────                    ────────────             │
  OpenClaw Gateway                Hermes Gateway           │
  ├── Channel: 飞书 WebSocket     ├── Channel: 飞书 Gateway│
  ├── Router: 前缀/account        ├── Router: LLM 语义     │
  ├── Agent: exp4-deepseek        ├── Agent: hermes-exp4   │
  │   (DeepSeek, 代码审查)        │   -deepseek (任务规划) │
  ├── Agent: exp4-qwen            ├── Agent: hermes-exp4   │
  │   (qwen3.6, 本地说明)         │   -qwen (安全复核)     │
  └── Config: ~\.openclaw\        └── Config: ~/.hermes/   │
                                                          │
  Provider: DeepSeek API ←──────→ Provider: Ollama 11434  │
                                                          │
  Logs ───────────────────────────────────────────────────┘
```
