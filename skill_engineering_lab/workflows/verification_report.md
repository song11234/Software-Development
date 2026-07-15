# 阶段四验证记录

## 挂载信息

| 项目 | 详情 |
|:--|:--|
| Skill 名称 | `genshin-code-guide` |
| Skill 路径 | `D:\skill_engineering_lab\skills\genshin-code-guide\SKILL.md` |
| Codex 挂载 | `%USERPROFILE%\.codex\skills\genshin-code-guide\SKILL.md` |
| CodeBuddy 挂载 | `%USERPROFILE%\.codebuddy\skills\genshin-code-guide\SKILL.md` |
| SKILL.md 大小 | 3383 bytes (约 50 行) |

## 五项验证逐项检查

对同一 Agent 会话中完成的"抓取 B站 + 天地游兑换码"任务进行验证：

### 1. 是否确认来源范围

| 检查项 | 实际表现 |
|:--|:--|
| 优先官方来源 | ✅ B站专栏 (official_social) 优先检测 |
| 说明第三方需核验 | ✅ 天地游标注为 third_party，confidence=low，status=unverified |
| 记录来源名称、URL、类型 | ✅ source_list.md + crawl_result.json 均已记录 |

### 2. 是否遵守抓取边界

| 检查项 | 实际表现 |
|:--|:--|
| 不要求登录 | ✅ 使用公开 API 和 urllib，未尝试登录 |
| 不绕过验证码 | ✅ 遇到 B站 API 风控 (412) 后换用公开专栏页 |
| 不访问非公开接口 | ✅ 仅使用 /x/polymer/web-dynamic/ 公开 API，未碰非公开端点 |
| 说明不适用自动抓取的来源 | ✅ B站动态 + 米游社标注为"JS 渲染，urllib 无法抓取" |

### 3. 是否抽取时间字段

| 检查项 | 实际表现 |
|:--|:--|
| 记录发布时间 | ✅ B站条目 published_at=2026-04-23T20:22:32 (来自 API) |
| 记录生效时间 | ✅ valid_from 字段已建立 |
| 记录失效时间 | ✅ B站条目 valid_until=2026-08-12 (从码中推导) |
| 记录抓取时间 | ✅ captured_at 字段已填充 |

### 4. 是否处理未知时间

| 检查项 | 实际表现 |
|:--|:--|
| 无法确定时标记 unknown | ✅ 天地游 4 条 published_at/valid_from/valid_until 全标 unknown |
| 不编造时间 | ✅ 未对无时间来源的条目编造任何时间 |
| 保留原文证据 | ✅ evidence_text 字段保留上下文 |

### 5. 是否自查

| 检查项 | 实际表现 |
|:--|:--|
| 检查来源链接 | ✅ source_url 全部完整 |
| 检查时间字段 | ✅ 逐项核对并修正（见上轮修复记录） |
| 检查状态标注 | ✅ 从 unknown 修正为 active_candidate/unverified |
| 检查可信度 | ✅ official_social→high, third_party→low |
| 安全提醒 | ✅ 报告中提醒第三方来源需核验 |

## 常见问题排查

| 可能问题 | 本实验状态 |
|:--|:--|
| SKILL.md 不在可发现目录 | ✅ 已挂载到 .codex/skills 和 .codebuddy/skills |
| name 使用特殊符号 | ✅ 纯英文+连字符 `genshin-code-guide` |
| description 太短 | ✅ 完整描述了触发场景、来源类型和任务范围 |
| 任务描述过于宽泛 | ✅ 明确限定"原神兑换码抓取""公开页面""时间抽取" |
| 平台不支持自动 Skill 发现 | ⚠️ CodeBuddy 通过 use_skill 工具触发，非自动发现 |

## 结论

5 项验证全部通过。Agent 在实际任务中遵循了 SKILL.md 定义的工作流程——确认来源范围、遵守抓取边界、抽取时间字段、标注 unknown、输出前自查。Skill 挂载成功，按预期工作。
