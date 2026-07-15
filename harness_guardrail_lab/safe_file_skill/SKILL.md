---
name: safe-file-assistant
description: 在实验 workspace 目录内安全读取、写入、追加和列出教学文件。仅用于课程实验中的受控文件操作；当请求涉及路径越界、危险扩展名、删除文件或系统命令时必须拒绝。
---

# Safe File Assistant

## 能力范围

- 读取 `workspace/` 内的 `.txt`、`.md`、`.json`、`.csv` 文件。
- 写入或追加不超过 2000 字符的教学文本。
- 列出 `workspace/` 内文件。

## 禁止行为

- 不读取 `workspace/` 之外的文件。
- 不执行系统命令。
- 不删除文件。
- 不处理 `.sh`、`.exe`、`.bat` 等危险扩展名。

## 调用流程

1. 将用户请求转换为工具请求字典。
2. 交给 Harness 的 `run_tool(request)`。
3. 如果返回 `ok=false`，把 `error` 作为反馈说明，不绕过 Harness。

## 与 Harness 的关系

- 本文档是能力说明（软约束），帮助 Agent 理解可以做什么。
- Harness 是代码级校验（硬约束），所有请求必须经过 `run_tool` 才能执行。
- 如果本文档的描述与 Harness 的实际策略不一致，以 Harness 的策略为准。
