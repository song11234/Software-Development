# 智能资料整理助手 — API 契约

## 服务信息

- **服务名**：智能资料整理助手 (Smart Document Organizer)
- **协议**：HTTP REST (JSON)
- **认证方式**：Bearer Token（在 `Authorization` 头中提供）

---

## 端点总览

| 方法 | 路径 | 说明 | 需要认证 |
|------|------|------|:--:|
| GET | `/` | 服务信息 | 否 |
| GET | `/health` | 健康检查 | 否 |
| POST | `/api/ingest` | 提交资料进行 AI 整理 | 是 |
| GET | `/api/documents` | 列出已整理资料 | 是 |
| GET | `/api/documents/{id}` | 查看单篇资料 | 是 |
| POST | `/api/search` | 关键词搜索资料 | 是 |
| POST | `/api/ask` | 基于资料的智能问答 (RAG) | 是 |
| DELETE | `/api/documents/{id}` | 删除资料 | 是 |

---

## 认证

所有需要认证的端点必须在请求头中携带：

```
Authorization: Bearer dev-local-token
```

- 缺少 Token → `401 {"detail": "缺少认证令牌"}`
- Token 无效 → `401 {"detail": "认证令牌无效"}`

---

## 端点详情

### 1. 健康检查

```
GET /health
```

**响应** `200`：
```json
{"status": "ok", "documents_count": 3}
```

### 2. 提交资料整理

```
POST /api/ingest
Authorization: Bearer {token}
Content-Type: application/json
```

**请求体**：
```json
{
  "title": "Python 异步编程入门指南",
  "content": "Python 中的异步编程主要基于 asyncio 库实现。通过 async/await 关键字..."
}
```

约束：
- `title`：1-200 字符
- `content`：10-50000 字符

**成功响应** `200`：
```json
{
  "ok": true,
  "document_id": "a1b2c3d4e5f6",
  "title": "Python 异步编程入门指南",
  "category": "技术/编程",
  "tags": ["Python", "异步编程", "asyncio"],
  "summary": "本文介绍 Python 异步编程基础...",
  "key_points": ["async/await 定义协程", "事件循环机制"],
  "token_usage": {"prompt_tokens": 200, "completion_tokens": 80, "total_tokens": 280},
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**错误**：
- `400` — 内容不合规
- `401` — 未认证
- `422` — 参数校验失败
- `429` — 频率超限

### 3. 资料列表

```
GET /api/documents?category=技术/编程&page=1&page_size=20
```

### 4. 关键词搜索

```
POST /api/search
```

**请求体**：
```json
{"query": "Python 异步", "category": "技术/编程", "top_k": 5}
```

### 5. 智能问答 (RAG)

```
POST /api/ask
```

**请求体**：
```json
{"question": "Python 异步编程的核心机制是什么？", "category": null}
```

**成功响应** `200`：
```json
{
  "ok": true,
  "answer": "Python 异步编程的核心是事件循环 (event loop)...",
  "sources": [
    {"document_id": "a1b2c3", "title": "Python 异步编程入门指南", "relevance_score": 12.5}
  ],
  "token_usage": {"prompt_tokens": 350, "completion_tokens": 60, "total_tokens": 410},
  "request_id": "..."
}
```

---

## 安全约束

- **频率限制**：默认 20 次/分钟/客户端
- **Token 预算**：单次请求预估不超过 4000 tokens
- **内容过滤**：检查用户输入合规性（可扩展）

## 交付物

- `src/` — 源代码
- `tests/` — pytest 自动化测试
- `index.html` — 前端页面
- `Dockerfile` — 容器化交付
- `skill/SKILL.md` — 本文档（API 契约）
