# 无 Skill 组 — 实验记录

## 初始提示词

```
请帮我从米游社、游戏官网或游戏资讯站抓取原神兑换码信息，并整理成表格。
```

---

## 执行过程

### 步骤 1：搜索 + 抓取

搜索 "原神 兑换码 2026 最新" 和 "Genshin Impact redeem codes 2026 July"。

- 米游社文章页：Loading.../SPA 页面，无法获取正文
- 官网 ys.mihoyo.com/news：Nuxt.js 渲染，无静态内容
- jiyx.com：反爬脚本拦截
- mobalytics.gg：403 Forbidden

成功获取到内容的来源：
- genshin-builds.com/cn/codes
- game8.co 的兑换码列表

---

## AI 输出（无 Skill 引导）

### 2026年7月原神可用兑换码

| 兑换码 | 奖励 | 来源 |
|:--|:--|:--|
| 8QD412QXCEU1 | 冒险家的经验 ×5 | genshin-builds.com |
| G9VY57AWQACW | 精锻用魔矿 ×10 | genshin-builds.com |
| FIGHTLIKESKIRK57 | 大英雄的经验 ×3 | genshin-builds.com |
| GS57YTSNLJ | 大英雄的经验 ×3 + 魔矿 ×5 + 冰玉碎屑 ×3 | genshin-builds.com |
| GIFTFROMSKIRK57 | 冰玉断片 ×3 + 魔矿 ×3 + 齿轮 ×3 | genshin-builds.com |
| ZT5RJ4AX4WYV | 冒险家的经验 ×5 | genshin-builds.com |
| LEGEDILJKSGM | 原石 ×60 + 冒险家经验 ×5 | game8.co |
| PFY1S40I88T9 | 摩拉 ×10000 + 冒险家经验 ×10 + 良矿 ×5 | game8.co |
| MIXF44DAP7HW | 原石 ×60 + 冒险家经验 ×5 | game8.co |
| ~~全球代码1~~ | 原石 ×100 | game8.co（标注6月22日过期） |

---

## 观察记录

| 观察点 | 表现 |
|:--|:--|
| 是否主动说明来源范围 | ❌ 未说明，直接从搜索结果中任意抓取 |
| 是否说明抓取边界 | ❌ 未提及边界，未区分 official/third_party |
| 是否记录来源链接 | ⚠️ 仅标注了域名，无完整 URL |
| 是否记录抓取时间 | ❌ 无 captured_at |
| 是否记录发布时间 | ⚠️ 含 2 条发布了日期（game8），其余缺失 |
| 是否抽取生效/失效时间 | ❌ 完全无 valid_from/valid_until |
| 是否标记未知 | ❌ 未标注任何 unknown/unverified |
| 是否编造信息 | ⚠️ 将 game8 的直播码（已过期）也列入 |
| 是否输出结构化 JSON | ❌ 仅表格，无结构化数据 |
| 去重 | ❌ 未做去重处理 |
| 结果可用性 | 低 — 缺时间字段、无来源分类、无可信度标注 |
