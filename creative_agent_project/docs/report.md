# 期末项目报告：智能资料整理助手

> 第99章 Vibe Coding 综合项目

## 一、项目背景

在日常工作和学习中，大量文档、笔记、资料以非结构化形式散落各处，查找和管理效率低下。本项目利用 AI 技术实现资料的自动整理：分类、标签化、摘要生成和基于知识库的智能问答。

## 二、技术方案

- **后端**：Python 3.11 + FastAPI
- **AI 引擎**：OpenAI 兼容 API（gpt-4o-mini）
- **存储**：文件型 JSON 存储（零数据库依赖）
- **前端**：纯 HTML5 + Vanilla JS
- **测试**：pytest + TestClient（ASGI 直连）
- **容器化**：Docker

## 三、AI 协助情况

| 阶段 | AI 协助内容 | 人工验证和修正 |
|------|-------------|---------------|
| 架构设计 | 提供模块划分方案 | 确认数据流、安全设计合理 |
| Workflow | 生成组织提示词和解析逻辑 | 调整 JSON 解析鲁棒性 |
| RAG | 实现检索→增强→生成流程 | 确认关键词检索权重合理性 |
| API 层 | 生成 FastAPI 路由 + 鉴权 | 补充异常处理和 422 校验 |
| 安全护栏 | 实现频率限制、token 预算 | 添加内容过滤器和拒答逻辑 |
| 测试 | 生成 pytest 用例 | 补充 rate limit 和边界测试 |
| 前端 | 生成完整 HTML UI | 调整样式和交互流程 |

## 四、功能验证

### 测试覆盖

```
tests/test_api.py — 15 个测试用例
├── test_health              — 健康检查 200
├── test_root                — API 导航
├── test_ingest_without_token — 无认证 401
├── test_list_without_token  — 无认证 401
├── test_ingest_empty_title  — 参数校验 422
├── test_ingest_short_content— 参数校验 422
├── test_ask_empty_question  — 参数校验 422
├── test_ingest_document     — 正常录入 200
├── test_ingest_then_list    — 录入后出现在列表
├── test_get_document        — 按 ID 获取
├── test_get_nonexistent     — 不存在 → 404
├── test_search_documents    — 关键词搜索
├── test_ask_question_rag    — RAG 问答
├── test_rate_limit_kicks_in — 频率限制 429
└── test_delete_document     — 删除资料
```

### 烟测覆盖

```
smoke_api.py — 7 步冒烟测试
├── health 检查
├── 无 Token 拒绝
├── 空标题校验
├── 正常录入
├── 资料列表
├── 关键词搜索
└── RAG 问答
```

## 五、部署方式

```bash
# 方式1：本地运行
pip install -r requirements.txt
# 编辑 .env 填入 API Key
python -m uvicorn src.app:app --host 0.0.0.0 --port 8000

# 方式2：bat 脚本
start.bat

# 方式3：Docker
docker build -t doc-organizer .
docker run -p 8000:8000 --env-file .env doc-organizer
```

## 六、项目亮点

1. **全栈闭环**：从 AI 工作流到 API 到前端，完整可运行
2. **安全护栏**：多层防护（认证、频率、预算、内容过滤）
3. **成本可控**：Token 用量实时追踪，预算硬限制
4. **轻量交付**：零数据库、纯文件存储，Docker 一行启动
5. **测试完备**：15 个自动化测试 + 冒烟测试
6. **RAG 实战**：完整的检索增强生成流程，含来源引用
