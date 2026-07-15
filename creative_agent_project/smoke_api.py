"""烟测脚本 —— 针对已部署服务进行快速冒烟验证。

对应知识点：第10章 烟测（需 uvicorn 运行中）。
用法：
    python smoke_api.py http://127.0.0.1:8000 dev-local-token
"""
import json
import sys
import urllib.request
import urllib.error


def req(url: str, method: str = "GET", token: str | None = None, body: dict | None = None):
    """发送 HTTP 请求，返回 (status_code, response_body_str)。"""
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    rq = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(rq, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)


def main():
    if len(sys.argv) < 3:
        print("用法: python smoke_api.py <BASE_URL> <TOKEN>")
        print("例如: python smoke_api.py http://127.0.0.1:8000 dev-local-token")
        sys.exit(1)

    base = sys.argv[1].rstrip("/")
    token = sys.argv[2]

    passed = 0
    failed = 0

    def check(name: str, status: int, expected: int, body: str = ""):
        nonlocal passed, failed
        preview = body[:120] if body else ""
        if status == expected:
            print(f"  [PASS] {name}  {status}  {preview}")
            passed += 1
        else:
            print(f"  [FAIL] {name}  got {status} expected {expected}  {preview}")
            failed += 1

    print(f"Smoke test: {base}\n")

    # 1. 健康检查
    s, b = req(f"{base}/health")
    check("health", s, 200, b)

    # 2. 无 Token → 401
    s, b = req(f"{base}/api/ingest", "POST", body={
        "title": "测试文档", "content": "这是一份测试文档的内容，包含不少于十个字符。"
    })
    check("ingest (no token)", s, 401, b)

    # 3. 空标题 → 422
    s, b = req(f"{base}/api/ingest", "POST", token=token, body={"title": "", "content": "测试内容..."})
    check("ingest (empty title)", s, 422, b)

    # 4. 正常录入
    s, b = req(f"{base}/api/ingest", "POST", token=token, body={
        "title": "资料整理测试",
        "content": "资料整理是指对文档、笔记等非结构化信息进行自动分类、摘要和标签化处理，以提升信息检索效率。"
    })
    check("ingest (valid)", s, 200, b)

    # 5. 资料列表
    s, b = req(f"{base}/api/documents", token=token)
    check("list documents", s, 200, b)

    # 6. 关键词搜索
    s, b = req(f"{base}/api/search", "POST", token=token, body={"query": "资料整理", "top_k": 3})
    check("search", s, 200, b)

    # 7. RAG 问答
    s, b = req(f"{base}/api/ask", "POST", token=token, body={"question": "什么是资料整理？"})
    check("ask (RAG)", s, 200, b)

    print(f"\n{'='*40}")
    print(f"结果: {passed} passed, {failed} failed")
    if failed > 0:
        print("有测试失败，请检查服务状态。")
        sys.exit(1)
    else:
        print("全部通过！")


if __name__ == "__main__":
    main()
