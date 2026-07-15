## Hermes 基础检查

- 安装方式：WSL2
- Hermes 版本：v0.18.2 (2026.7.7.2) · upstream bd740f20
- `hermes doctor` 结果：✅ 通过，仅 1 个低优先级建议（`hermes setup` 补齐可选工具）；API Connectivity 中 DeepSeek ✓
- 模型 Provider：DeepSeek
- 模型名或 Custom endpoint：DeepSeek API（已通过 `hermes model` 选择 DeepSeek Provider 并配置 API Key）
- CLI 对话是否成功：✅ 成功，`hermes chat -q "用一句话介绍 AgentOps"` 6 秒内返回完整回答
- 配置目录或数据目录：`~/.hermes/`（含 `config.yaml`、`.env`、`sessions/`、`logs/`、`skills/`、`memories/`）
- 遇到的问题：Windows 原生 `hermes` 命令不可用（PowerShell 中无法识别），在 WSL2 Ubuntu 中安装后正常使用
