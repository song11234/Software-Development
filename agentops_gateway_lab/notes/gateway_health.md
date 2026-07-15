## 网关健康检查

- 框架：OpenClaw
- 版本：2026.6.11
- Gateway 状态：running（pid 50432）
- 监听地址：127.0.0.1:18789
- 连接探测：ok
- 能力状态：connected-no-operator-scope
- 服务类型：Scheduled Task（已注册）
- 配置文件：`~\.openclaw\openclaw.json`
- 日志路径：`~\AppData\Local\Temp\openclaw\openclaw-2026-07-14.log`
- Dashboard：http://127.0.0.1:18789/
- 说明：只能本机访问（loopback-only）

### 启动命令
```powershell
openclaw gateway install
openclaw gateway start
openclaw gateway status
```

### 遇到的问题
- `openclaw configure gateway --log-level debug` 命令在新版本中不支持（需交互式配置或跳过）
- 计划任务不报告 running 状态，但实际监听端口 18789 已验证
