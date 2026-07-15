"""Pydantic 数据模型 —— API 请求/响应契约。

对应知识点：第10章 API 契约设计、第02章 Pydantic 校验、第06章提示词工程中的 schema 定义。
"""
from typing import Optional
from pydantic import BaseModel, Field


# ── 资料录入 ──

class IngestRequest(BaseModel):
    """提交待整理的资料。"""
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="资料标题",
        examples=["Python异步编程入门"]
    )
    content: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="资料正文",
        examples=["Python 中的异步编程主要通过 asyncio 模块实现..."]
    )


class IngestResponse(BaseModel):
    """AI 整理后的资料结果。"""
    ok: bool
    document_id: str
    title: str
    category: str
    tags: list[str]
    summary: str
    key_points: list[str]
    token_usage: dict
    request_id: str


# ── 资料查询 ──

class ListResponse(BaseModel):
    """资料列表。"""
    documents: list[dict]
    total: int
    page: int
    page_size: int


class SearchRequest(BaseModel):
    """关键词搜索。"""
    query: str = Field(..., min_length=1, max_length=500)
    category: Optional[str] = Field(default=None, description="按分类过滤")
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    """单条搜索结果。"""
    document_id: str
    title: str
    category: str
    summary: str
    relevance_score: float


class SearchResponse(BaseModel):
    """搜索结果列表。"""
    results: list[SearchResult]
    query: str
    total_found: int


# ── 知识问答 (RAG) ──

class AskRequest(BaseModel):
    """RAG 问答请求。"""
    question: str = Field(..., min_length=1, max_length=1000)
    category: Optional[str] = Field(default=None)


class DocumentSource(BaseModel):
    """引用来源。"""
    document_id: str
    title: str
    relevance_score: float


class AskResponse(BaseModel):
    """RAG 问答响应。"""
    ok: bool
    answer: str
    sources: list[DocumentSource]
    token_usage: dict
    request_id: str


# ── 通用 ──

class ErrorResponse(BaseModel):
    """统一错误响应。"""
    detail: str
    error_code: str = "UNKNOWN"
