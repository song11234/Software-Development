import os
import time
import uuid

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from workflow import run_ai_workflow


API_TOKEN_ENV = "COURSE_API_TOKEN"

app = FastAPI(title="Modern Software AI API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000", "null"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


class AskRequest(BaseModel):
    """请求体模型限制问题长度，避免无边界输入。"""

    question: str = Field(min_length=1, max_length=500)


class AskResponse(BaseModel):
    """响应体模型让调用方知道返回字段。"""

    answer: str
    sources: list[str]
    ok: bool
    request_id: str
    elapsed_ms: int


def expected_token() -> str:
    """从环境变量读取 Token，缺失时返回明确服务端错误。"""

    token = os.getenv(API_TOKEN_ENV)
    if not token:
        raise HTTPException(status_code=500, detail=f"{API_TOKEN_ENV} is not configured")
    return token


def check_token(authorization: str | None) -> None:
    """检查 Authorization Header 是否为 Bearer Token。"""

    expected = f"Bearer {expected_token()}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="invalid token")


@app.get("/health")
def health() -> dict:
    """健康检查不需要 Token，便于容器和脚本确认服务存活。"""

    return {"status": "ok"}


@app.post("/api/ask", response_model=AskResponse)
def ask(payload: AskRequest, request: Request, authorization: str | None = Header(default=None)) -> dict:
    """核心业务接口：鉴权后调用本地 AI 工作流。"""

    check_token(authorization)
    start = time.perf_counter()
    result = run_ai_workflow(payload.question)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    return {
        **result,
        "request_id": request.headers.get("X-Request-ID", str(uuid.uuid4())),
        "elapsed_ms": elapsed_ms,
    }
