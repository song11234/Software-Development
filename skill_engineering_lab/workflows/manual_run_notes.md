# 手动工作流记录

## 任务名称

原神官方兑换码与活动码信息抓取。

## 为什么需要 Skill

每次抓取原神兑换码信息时，都需要重复说明来源范围、抓取边界、兑换码格式、生效时间、失效时间、来源可信度和防诈骗要求。

## 期望 Agent 做到

- 优先抓取官方或高可信公开来源，例如米游社公开帖子、游戏官网公告、HoYoLAB 公告、官方社交媒体公告和课堂指定游戏资讯站。
- 抓取前检查页面是否公开可访问，遵守访问频率和站点规则。
- 从正文中抽取兑换码、发布时间、生效时间、失效时间、适用服务器和来源链接。
- 对未说明失效时间的信息标记为 `unknown`，不直接声称"永久有效"。
- 对第三方来源进行可信度标注，并提醒同学不要点击要求登录、付费、加群或下载不明文件的链接。

## 工作流记录

### 任务

从 B站（bilibili.com）原神官方相关公开页面抓取兑换码信息，抽取兑换码、发布时间、生效时间、失效时间，标注来源类型和可信度，输出符合数据字段约定的 JSON。

### 输入资料

| 来源 | 类型 | URL | 访问方式 |
|:--|:--|:--|:--|
| B站专栏 cv48145110 | official_social | https://www.bilibili.com/read/cv48145110 | web_fetch + B站文章 API |
| B站动态 1044181535496863751 | official_social | https://t.bilibili.com/1044181535496863751 | B站动态详情 API |
| 天地游-兑换码合集 | third_party | https://www.tiandiyou.com/youxigonglue/6041.html | urllib 直接抓取 HTML |

#### 关键原文证据

- B站专栏 API 返回：`"title":"原神兑换码大全2026最新4月亲测有效","summary":"其中GENSHINGIFT等永久码可随时兑换...版本前瞻'向至冬20260812'..."`
- 天地游 HTML：`<p>其中包括GENSHINGIFT和KT6AX6JQS5UW...</p>`（4 个候选码，无时间标注）
- B站动态 API：`412 Precondition Failed`（风控，无法直接获取正文）

### 实际步骤

1. 通过 `web_search` 搜索 "原神 兑换码 bilibili 动态"，定位 B站官方相关页面
2. 尝试直接 `web_fetch` 访问 B站动态页 `t.bilibili.com/1044181535496863751`，无法获取 JS 渲染内容
3. 改用 B站公开 API `api.bilibili.com/x/polymer/web-dynamic/v1/detail?id=...`，返回 412 被风控
4. 改用 B站文章 API `api.bilibili.com/x/article/view?id=48145110`，成功获取专栏正文
5. 从专栏摘要中抽取兑换码候选："向至冬20260812"（含日期推断：valid_until → 2026-08-12）
6. 用 urllib 抓取天地游 HTML 页面，正则抽取 4 个疑似兑换码
7. 发现 Python `\b` 在中英文交界失效，改为手工从文本中提取
8. 组装为符合 11 字段约定的 JSON，区分 B站（high/active_candidate）与天地游（low/unverified）
9. 对比字段约定，发现缺少 `time_evidence` 冗余字段 + `status` 错误标注 → 修正
10. 最终产出 `crawl_result.json`，共 5 条记录

### 中途失败或返工

| 问题 | 原因 | 修正方式 |
|:--|:--|:--|
| B站动态页面 `web_fetch` 返回空白 | SPA 页面，JS 动态渲染，纯 HTTP 请求拿不到正文 | 改用 B站文章 API（无需 JS 渲染） |
| B站动态 API 返回 412 | B站风控机制，检测到非浏览器请求 | 记录为 "当前来源不适合自动抓取"，换用专栏页 |
| 抓取脚本返回 0 条结果 | B站和米游社都是 SPA，urllib 未提取到有效文本 | 手工从 API 响应中提取 + 直接解析天地游 HTML |
| 正则 `\b[A-Z0-9]{8,20}\b` 无法匹配中文环境 | Python 3 将 CJK 字符视为 `\w`，`\b` 边界失效 | 改用 Python 代码手工提取，记录为教学发现 |
| 初次 JSON 多了 `time_evidence` 字段 | 未严格对照字段约定表 | 删除冗余字段，修正 `status` 标注值 |
| 来源与条目混淆 | 天地游 4 条错标为 B站来源 | 逐条核对 source_name/source_type/source_url |

### 最终产物

- `workflows/source_list.md` — 3 个来源的清单（名称、类型、URL、访问状态）
- `workflows/crawl_result.json` — 5 条结构化记录，严格符合 11 字段约定

### 可复用经验

**应该固定下来的步骤：**
- 抓取前先搜索定位公开页面 URL，确认页面类型（SPA/静态/API）
- SPA 页面优先找公开 API，API 不可用时标记为 "不适合自动抓取"
- 第三方来源永远标 `confidence=low`、`status=unverified`
- 码中含日期线索时（如 "20260812"），用于推导 `valid_until`
- 输出后逐条对照字段约定表自检

**需要视情况判断的内容：**
- 不同网站的风控策略不同，没有统一绕过方式
- 兑换码格式不统一（英文码 vs 中文码），正则需根据实际调整
- 时间解析依赖原文表达方式，无法完全自动化
