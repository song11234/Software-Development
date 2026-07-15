"""FastAPI 应用入口 —— 智能资料整理助手 API 服务。

对应知识点：
- 第02章：SaaS 到 AI Agent，FastAPI 服务 + Token 鉴权
- 第07章：Harness 安全护栏（频率限制、内容过滤）
- 第08章：Token 成本控制
- 第10章：AI 应用 API 化与全栈交付
"""
import uuid
import traceback
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.config import get_config
from src.models import (
    IngestRequest, IngestResponse,
    ListResponse, SearchRequest, SearchResponse, SearchResult,
    AskRequest, AskResponse, DocumentSource,
    ErrorResponse,
)
from src.store import DocumentStore
from src.workflow import organize_document
from src.rag import answer_question
from src.safety import RateLimiter, TokenBudget, ContentFilter

# ── 应用初始化 ──

config = get_config()
app = FastAPI(
    title="智能资料整理助手",
    description="基于 AI 的资料自动分类、摘要、标签化和知识问答系统",
    version="1.0.0",
)

# CORS（第10章：支持前端直接调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全组件（第07章）
security = HTTPBearer(auto_error=False)
rate_limiter = RateLimiter(max_per_minute=config.rate_limit_per_minute)
token_budget = TokenBudget(max_tokens=config.max_tokens_per_request)

# 数据层
store = DocumentStore(base_dir=config.documents_dir)


# ── 鉴权依赖（第02章/第10章：Token 认证） ──

def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """验证 Bearer Token。"""
    if credentials is None:
        raise HTTPException(status_code=401, detail="缺少认证令牌，请在 Authorization 头中提供 Bearer Token")
    if credentials.credentials != config.api_token:
        raise HTTPException(status_code=401, detail="认证令牌无效")
    return credentials.credentials


def get_client_id(request: Request) -> str:
    """从请求中提取客户端标识（用于频率限制）。"""
    return request.client.host if request.client else "unknown"


# ── 全局异常处理 ──

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """统一异常处理，避免内部错误泄漏到客户端。"""
    error_id = str(uuid.uuid4())[:8]
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"服务内部错误 (ID: {error_id})",
            "error_code": "INTERNAL_ERROR",
        },
    )


# ── API 路由 ──

@app.get("/health")
def health():
    """健康检查端点。

    使用方式：curl http://127.0.0.1:8000/health
    对应第10章：部署前的健康检查机制。
    """
    return {"status": "ok", "documents_count": store.count()}


@app.get("/")
def root():
    """根路径 —— 返回 API 导航信息。"""
    return {
        "service": "智能资料整理助手",
        "version": "1.0.0",
        "endpoints": {
            "GET  /health": "健康检查",
            "POST /api/ingest": "提交资料进行 AI 整理",
            "GET  /api/documents": "列出已整理资料",
            "GET  /api/documents/{id}": "查看单篇资料",
            "POST /api/search": "关键词搜索资料",
            "POST /api/ask": "基于资料的智能问答 (RAG)",
            "DELETE /api/documents/{id}": "删除资料",
        },
        "auth": "在 Authorization 头中提供 Bearer Token",
    }


@app.post("/api/ingest", response_model=IngestResponse)
def ingest(
    body: IngestRequest,
    request: Request,
    _token: str = Depends(verify_token),
):
    """提交资料进行 AI 整理。

    流程（第02章 Agent 工作流、第07章安全护栏）：
    1. 频率限制检查
    2. 内容安全检查
    3. AI 整理：分类 → 标签 → 摘要 → 要点
    4. 存储到资料库
    5. 返回结果
    """
    request_id = str(uuid.uuid4())
    client_id = get_client_id(request)

    # 第07章：频率限制
    ok, msg = rate_limiter.check(client_id)
    if not ok:
        raise HTTPException(status_code=429, detail=msg)

    # 第07章：内容安全检查
    ok, err = ContentFilter.check_input(body.content)
    if not ok:
        raise HTTPException(status_code=400, detail=err or "内容不合规")

    # 第08章：Token 预算预估
    estimated_tokens = len(body.content) // 2 + 500
    ok, msg = token_budget.check(request_id, estimated_tokens)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    # 第02章：调用 AI 工作流
    try:
        result = organize_document(title=body.title, content=body.content)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI 服务调用失败: {str(e)}")

    organized = result["result"]
    usage = result["token_usage"]

    # 存储到资料库
    doc_id = str(uuid.uuid4())[:12]
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "document_id": doc_id,
        "title": body.title,
        "content": body.content,
        "category": organized.get("category", "未分类"),
        "tags": organized.get("tags", []),
        "summary": organized.get("summary", ""),
        "key_points": organized.get("key_points", []),
        "token_usage": usage,
        "created_at": now,
    }
    store.save(doc_id, doc)

    # 第08章：记录实际 token 用量
    token_budget.record(request_id, usage.get("total_tokens", 0))

    return IngestResponse(
        ok=True,
        document_id=doc_id,
        title=body.title,
        category=doc["category"],
        tags=doc["tags"],
        summary=doc["summary"],
        key_points=doc["key_points"],
        token_usage=usage,
        request_id=request_id,
    )


@app.get("/api/documents", response_model=ListResponse)
def list_documents(
    category: Optional[str] = Query(default=None, description="按分类过滤"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _token: str = Depends(verify_token),
):
    """列出已整理的资料列表，支持分页和分类过滤。"""
    docs, total = store.list_all(category=category, page=page, page_size=page_size)
    return ListResponse(documents=docs, total=total, page=page, page_size=page_size)


@app.get("/api/documents/{doc_id}")
def get_document(doc_id: str, _token: str = Depends(verify_token)):
    """查看单篇资料的完整内容。"""
    doc = store.get(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"资料不存在: {doc_id}")
    return {"ok": True, "document": doc}


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str, _token: str = Depends(verify_token)):
    """删除资料。"""
    ok = store.delete(doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"资料不存在: {doc_id}")
    return {"ok": True, "deleted": doc_id}


@app.post("/api/search", response_model=SearchResponse)
def search(
    body: SearchRequest,
    _token: str = Depends(verify_token),
):
    """关键词搜索已整理资料。

    实现：基于标题/摘要/标签/正文的加权关键词匹配（第03章检索策略）。
    """
    results = store.search(body.query, category=body.category, top_k=body.top_k)
    return SearchResponse(
        results=[SearchResult(**r) for r in results],
        query=body.query,
        total_found=len(results),
    )


@app.post("/api/ask", response_model=AskResponse)
def ask(
    body: AskRequest,
    request: Request,
    _token: str = Depends(verify_token),
):
    """基于资料库的智能问答 (RAG)。

    对应第03章完整流程：检索 → 构建上下文 → LLM 生成 → 返回来源引用。
    """
    request_id = str(uuid.uuid4())
    client_id = get_client_id(request)

    # 第07章：频率限制
    ok, msg = rate_limiter.check(client_id)
    if not ok:
        raise HTTPException(status_code=429, detail=msg)

    # 第07章：内容安全检查
    ok, err = ContentFilter.check_input(body.question)
    if not ok:
        raise HTTPException(status_code=400, detail=err or "问题内容不合规")

    try:
        result = answer_question(
            question=body.question,
            store=store,
            category=body.category,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI 问答服务调用失败: {str(e)}")

    return AskResponse(
        ok=result["ok"],
        answer=result["answer"],
        sources=[DocumentSource(**s) for s in result["sources"]],
        token_usage=result["token_usage"],
        request_id=request_id,
    )
