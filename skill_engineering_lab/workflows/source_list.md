# 抓取来源清单

| source_name | source_type | url | note |
| :-- | :-- | :-- | :-- |
| B站-原神兑换码专栏 | official_social | https://www.bilibili.com/read/cv48145110 | 2026-04-23发布，B站 API 可获取正文，含"向至冬20260812" |
| B站-5.5前瞻动态 | official_social | https://t.bilibili.com/1044181535496863751 | B站动态（JS渲染），2025-03-14发布，含5.5版本前瞻码3个 |
| 米游社-2026跨年兑换码 | official_community | https://www.miyoushe.com/ys/article/71958768 | 米游社公开帖子（JS渲染），2025-12-31发布 |
| 天地游-兑换码合集 | third_party | https://www.tiandiyou.com/youxigonglue/6041.html | 第三方游戏站，含 GENSHINGIFT 等码，HTML可直接抓取文本 |

## 抓取结果

详见 `workflows/crawl_result.json` — 通过 urllib + TextExtractor 从天地游获取到 4 个候选码；
B站专栏通过 API 获取到 1 个含中文的候选码。

## 发现的教学点

1. **B站/米游社为 JS 渲染 SPA**：urllib 只能获取空壳 HTML，正文需要浏览器渲染或 API
2. **Python re `\b` 与中文边界问题**：Python 3 默认 `re.U` 将中文字符视为 `\w`，导致 `\b[A-Z0-9]{8,20}\b` 在中英文交界处失效
3. **第三方来源需标注低可信**：天地游等第三方站的兑换码需人工核验
