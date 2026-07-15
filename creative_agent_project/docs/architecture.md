# 系统架构文档

## 项目概述

**智能资料整理助手 (Smart Document Organizer)** 是一个基于 AI 的资料自动分类、摘要和知识问答系统。用户提交原始文档，AI 自动进行分类、打标签、生成摘要和提取关键要点，并支持基于已整理资料库的 RAG 智能问答。

## 技术架构

```
┌─────────────────────────────────────────────────┐
│                   index.html                    │  ← 前端（第10章）
│           (HTML5 + Vanilla JS + Fetch)          │
└──────────────────────┬──────────────────────────┘
                       │ HTTP/JSON (CORS)
┌──────────────────────▼──────────────────────────┐
│                  src/app.py                     │  ← API 层（第02/10章）
│         FastAPI + Bearer Token 鉴权             │
├────────────┬────────────┬────────────┬──────────┤
│            │            │            │          │
│  workflow  │    rag     │   store    │  safety  │
│  第02/06章  │  第03章    │  第03章     │  第07章   │
│            │            │            │          │
└────────────┴──────┬─────┴────────────┴──────────┘
                    │
┌───────────────────▼─────────────────────────────┐
│              OpenAI Compatible API               │
│              (gpt-4o-mini / 其他模型)             │
└─────────────────────────────────────────────────┘
```

## 数据流

### 1. 资料录入流程 (Ingest)

```
用户提交 {title, content}
  → ContentFilter 安全检查
  → RateLimiter 频率检查
  → TokenBudget 预算检查
  → Workflow.organize_document()
    → OpenAI API: 分类 + 标签 + 摘要 + 要点
  → DocumentStore.save() 持久化
  → 返回 IngestResponse
```

### 2. RAG 问答流程 (Ask)

```
用户提交 {question}
  → DocumentStore.search() 关键词检索
  → 构建上下文 (Top-3 文档)
  → OpenAI API: 基于上下文生成回答
  → 返回 AskResponse {answer, sources}
```

## 存储设计

```
data/documents/
├── index.json          # 元数据索引
├── {doc_id}.json       # 文档完整内容
```

- 零外部依赖，纯文件存储
- 索引加载到内存，写操作持久化到磁盘

## 安全设计

| 层次 | 机制 | 文件 |
|------|------|------|
| 认证 | Bearer Token | app.py |
| 频率限制 | 滑动窗口 20次/分钟 | safety.py |
| Token 预算 | 单次 ≤ 4000 tokens | safety.py |
| 内容过滤 | 敏感词检测 | safety.py |
| 拒答机制 | RAG 不足时明确拒绝 | rag.py |

## 对应课程知识点映射

| 章节 | 知识点 | 在本项目中的体现 |
|------|--------|------------------|
| 01 | TDD / pytest / CI | `tests/test_api.py` 15个测试用例 |
| 02 | SaaS→AI Agent / FastAPI | `app.py` Token 鉴权 + AI 工具调用 |
| 03 | RAG / 知识增强问答 | `rag.py` 检索→增强→生成 |
| 04 | 多模型网关 | 通过环境变量切换模型 |
| 05 | Skill 工程 | `skill/SKILL.md` API 契约 |
| 06 | 提示词工程 | `workflow.py` 结构化 prompt |
| 07 | Harness 安全护栏 | `safety.py` 频率限制+内容过滤+预算 |
| 08 | Token 成本控制 | Token 预估+实际用量追踪 |
| 09 | 多 Agent 工作流编排 | Ingest→Organize→Store 流水线 |
| 10 | API 化全栈交付 | FastAPI + 前端 + Docker + 烟测 |
