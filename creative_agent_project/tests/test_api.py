"""API 自动化测试套件 —— pytest + TestClient。

对应知识点：
- 第01章：TDD 与 CI/CD 全链路实战
- 第10章：TestClient 直连 ASGI，无需启动服务
- 覆盖：200/401/404/422/429 场景
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


# ── 自动夹具：mock API key 校验 + 重置全局状态 ──

@pytest.fixture(autouse=True)
def _mock_api_key_valid():
    """自动 mock is_api_key_valid() 为 True，让测试不依赖真实 API Key。"""
    with patch("src.config.AppConfig.is_api_key_valid", return_value=True):
        yield


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """每个测试前重置频率限制器，避免测试间相互影响。"""
    from src.app import rate_limiter
    rate_limiter._windows.clear()
    yield


# ── 测试数据夹具 ──

AUTH_HEADERS = {"Authorization": "Bearer dev-local-token"}

SAMPLE_DOC = {
    "title": "Python 异步编程入门指南",
    "content": (
        "Python 中的异步编程主要基于 asyncio 库实现。"
        "通过 async/await 关键字可以定义协程函数。"
        "事件循环 (event loop) 是异步编程的核心，它负责调度和执行协程。"
        "asyncio.gather() 可以并发执行多个协程，提高 I/O 密集型任务的性能。"
        "常见的异步场景包括网络请求、文件读写、数据库查询等。"
    ),
}

MOCK_AI_RESULT = {
    "category": "技术/编程",
    "tags": ["Python", "异步编程", "asyncio", "并发"],
    "summary": "本文介绍 Python 异步编程基础，涵盖 asyncio 库、async/await 语法和事件循环的用法。",
    "key_points": [
        "async/await 定义协程函数",
        "事件循环负责调度协程",
        "asyncio.gather 实现并发",
        "适用于 I/O 密集型任务",
    ],
}


def _mock_openai_response(json_text: str, prompt_tokens: int = 100, completion_tokens: int = 50):
    """构造模拟的 OpenAI API 响应。"""
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = json_text
    mock_resp.usage.prompt_tokens = prompt_tokens
    mock_resp.usage.completion_tokens = completion_tokens
    mock_resp.usage.total_tokens = prompt_tokens + completion_tokens
    return mock_resp


# ── 第10章模式：健康检查 ──

def test_health():
    """GET /health → 200。"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "documents_count" in data


def test_root():
    """GET / → 200，返回 API 导航信息。"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "endpoints" in data


# ── 第10章模式：认证测试 401 ──

def test_ingest_without_token_returns_401():
    """无 Token → 401。"""
    response = client.post("/api/ingest", json=SAMPLE_DOC)
    assert response.status_code == 401


def test_list_without_token_returns_401():
    """无 Token 列表 → 401。"""
    response = client.get("/api/documents")
    assert response.status_code == 401


# ── 第10章模式：参数校验 422 ──

def test_ingest_empty_title_returns_422():
    """空标题 → 422。"""
    response = client.post("/api/ingest", json={"title": "", "content": "测试内容..."}, headers=AUTH_HEADERS)
    assert response.status_code == 422


def test_ingest_short_content_returns_422():
    """内容过短 → 422。"""
    response = client.post("/api/ingest", json={"title": "测试", "content": "短"}, headers=AUTH_HEADERS)
    assert response.status_code == 422


def test_ask_empty_question_returns_422():
    """空问题 → 422。"""
    response = client.post("/api/ask", json={"question": ""}, headers=AUTH_HEADERS)
    assert response.status_code == 422


# ── 核心功能测试（mock AI 调用） ──

@patch("src.workflow.OpenAI")
def test_ingest_document(mock_openai_class):
    """POST /api/ingest → 200，验证 AI 整理后入库。"""
    import json as _json
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_openai_response(
        _json.dumps(MOCK_AI_RESULT, ensure_ascii=False)
    )
    mock_openai_class.return_value = mock_client

    response = client.post("/api/ingest", json=SAMPLE_DOC, headers=AUTH_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["title"] == SAMPLE_DOC["title"]
    assert data["category"] == "技术/编程"
    assert "Python" in data["tags"]
    assert len(data["key_points"]) >= 3
    assert "document_id" in data
    assert "request_id" in data
    assert data["token_usage"]["total_tokens"] > 0


@patch("src.workflow.OpenAI")
def test_ingest_then_list(mock_openai_class):
    """准入资料后应出现在列表中。"""
    import json as _json
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_openai_response(
        _json.dumps(MOCK_AI_RESULT, ensure_ascii=False)
    )
    mock_openai_class.return_value = mock_client

    ingest_resp = client.post("/api/ingest", json=SAMPLE_DOC, headers=AUTH_HEADERS)
    assert ingest_resp.status_code == 200
    doc_id = ingest_resp.json()["document_id"]

    list_resp = client.get("/api/documents", headers=AUTH_HEADERS)
    assert list_resp.status_code == 200
    docs = list_resp.json()["documents"]
    assert any(d["document_id"] == doc_id for d in docs)


@patch("src.workflow.OpenAI")
def test_get_document(mock_openai_class):
    """GET /api/documents/{id} → 200，返回完整文档。"""
    import json as _json
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_openai_response(
        _json.dumps(MOCK_AI_RESULT, ensure_ascii=False)
    )
    mock_openai_class.return_value = mock_client

    ingest_resp = client.post("/api/ingest", json=SAMPLE_DOC, headers=AUTH_HEADERS)
    doc_id = ingest_resp.json()["document_id"]

    get_resp = client.get(f"/api/documents/{doc_id}", headers=AUTH_HEADERS)
    assert get_resp.status_code == 200
    assert get_resp.json()["document"]["title"] == SAMPLE_DOC["title"]


def test_get_nonexistent_document_returns_404():
    """不存在的资料 → 404。"""
    response = client.get("/api/documents/nonexistent-id", headers=AUTH_HEADERS)
    assert response.status_code == 404


@patch("src.workflow.OpenAI")
def test_search_documents(mock_openai_class):
    """POST /api/search → 200，关键词检索。"""
    import json as _json
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_openai_response(
        _json.dumps(MOCK_AI_RESULT, ensure_ascii=False)
    )
    mock_openai_class.return_value = mock_client

    client.post("/api/ingest", json=SAMPLE_DOC, headers=AUTH_HEADERS)

    search_resp = client.post(
        "/api/search",
        json={"query": "Python 异步", "top_k": 5},
        headers=AUTH_HEADERS,
    )
    assert search_resp.status_code == 200
    data = search_resp.json()
    assert len(data["results"]) >= 1
    assert data["query"] == "Python 异步"


@patch("src.rag.OpenAI")
@patch("src.workflow.OpenAI")
def test_ask_question_rag(mock_workflow_openai, mock_rag_openai):
    """POST /api/ask → 200，RAG 问答返回引用来源。"""
    import json as _json

    # Mock workflow
    mock_wf = MagicMock()
    mock_wf.chat.completions.create.return_value = _mock_openai_response(
        _json.dumps(MOCK_AI_RESULT, ensure_ascii=False)
    )
    mock_workflow_openai.return_value = mock_wf

    # 先摄入文档
    client.post("/api/ingest", json=SAMPLE_DOC, headers=AUTH_HEADERS)

    # Mock RAG
    mock_rag = MagicMock()
    mock_rag.chat.completions.create.return_value = _mock_openai_response(
        "asyncio 是 Python 的异步编程核心库，通过事件循环调度协程实现并发。", 150, 30
    )
    mock_rag_openai.return_value = mock_rag

    ask_resp = client.post(
        "/api/ask",
        json={"question": "Python 异步编程的核心是什么？"},
        headers=AUTH_HEADERS,
    )
    assert ask_resp.status_code == 200
    data = ask_resp.json()
    assert data["ok"] is True
    assert len(data["answer"]) > 0
    assert "asyncio" in data["answer"].lower() or "Python" in data["answer"]


# ── 第07章：频率限制测试 ──

@patch("src.workflow.OpenAI")
def test_rate_limit_kicks_in(mock_openai_class):
    """连续大量请求应触发频率限制 429。

    默认限制 20次/分钟，发 25 次请求验证。
    """
    import json as _json
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_openai_response(
        _json.dumps(MOCK_AI_RESULT, ensure_ascii=False)
    )
    mock_openai_class.return_value = mock_client

    statuses = []
    for _ in range(25):
        resp = client.post("/api/ingest", json=SAMPLE_DOC, headers=AUTH_HEADERS)
        statuses.append(resp.status_code)

    # 应有至少一次 429（前20次成功，后5次被限）
    assert 429 in statuses, f"Expected 429 in responses, got: {statuses[:5]}...{statuses[-5:]}"


# ── 删除测试 ──

@patch("src.workflow.OpenAI")
def test_delete_document(mock_openai_class):
    """DELETE /api/documents/{id} → 200。"""
    import json as _json
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_openai_response(
        _json.dumps(MOCK_AI_RESULT, ensure_ascii=False)
    )
    mock_openai_class.return_value = mock_client

    ingest_resp = client.post("/api/ingest", json=SAMPLE_DOC, headers=AUTH_HEADERS)
    doc_id = ingest_resp.json()["document_id"]

    del_resp = client.delete(f"/api/documents/{doc_id}", headers=AUTH_HEADERS)
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] == doc_id

    get_resp = client.get(f"/api/documents/{doc_id}", headers=AUTH_HEADERS)
    assert get_resp.status_code == 404
