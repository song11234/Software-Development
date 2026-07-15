import json
from datetime import date
from pathlib import Path

import chromadb

from simple_vector import tokenize
from student_info import print_student_id

COLLECTION_NAME = "genshin_rag"
TERMS = [
    "原神", "玩家", "旅行者", "提瓦特", "祈愿", "原石", "纠缠之缘", "相遇之缘",
    "角色", "武器", "养成", "等级", "天赋", "命之座", "圣遗物",
    "主属性", "副属性", "攻击", "防御", "生命", "元素", "反应",
    "蒸发", "融化", "超载", "感电", "扩散", "原粹树脂", "体力",
    "地脉", "秘境", "首领", "奖励", "活动", "建议", "优先",
]


def embed(text: str) -> list[float]:
    """把文本转换为固定长度向量，模拟真实 Embedding 写入向量库。"""
    tokens = set(tokenize(text))
    return [1.0 if term.lower() in tokens else 0.0 for term in TERMS]


def parse_date(value: str | None):
    """解析日期字符串，用于向量库元数据的时效判断。"""
    if not value:
        return None
    return date.fromisoformat(value)


def is_expired(metadata: dict, today: date | None = None) -> bool:
    """根据 expires_at 给 ChromaDB 元数据写入 expired 标记。"""
    today = today or date.today()
    expires_at = parse_date(metadata.get("expires_at"))
    return bool(expires_at and expires_at < today)


def get_client(path: str = "index/chroma_db"):
    """创建 ChromaDB 持久化客户端，数据会保存在本地目录。"""
    return chromadb.PersistentClient(path=path)


def get_collection(client):
    """获取或创建原神 RAG 集合。"""
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def build_chroma_store(corpus_path: str = "docs/genshin_corpus.json") -> None:
    """把语料批量写入 ChromaDB，形成真实可查询的向量集合。"""
    client = get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = get_collection(client)
    corpus = json.loads(Path(corpus_path).read_text(encoding="utf-8"))

    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for doc in corpus["documents"]:
        for index, text in enumerate(doc["content"], start=1):
            chunk_id = f"{doc['doc_id']}#c{index:03d}"
            metadata = {
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "source": doc["source"],
                "updated_at": doc["updated_at"],
                "expires_at": doc["expires_at"],
                "roles": ",".join(doc["roles"]),
                "role_student": "student" in doc["roles"],
                "role_teacher": "teacher" in doc["roles"],
                "claim_key": doc.get("claim_key") or "",
                "claim_value": doc.get("claim_value") or "",
            }
            metadata["expired"] = is_expired(metadata)

            ids.append(chunk_id)
            documents.append(text)
            embeddings.append(embed(text))
            metadatas.append(metadata)

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    print(f"chroma_records={collection.count()}")


def build_where(role: str, include_expired: bool) -> dict:
    """构造 ChromaDB 元数据过滤条件，先过滤权限和过期状态。"""
    conditions = [{f"role_{role}": True}]
    if not include_expired:
        conditions.append({"expired": False})
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def search_chroma_db(
    question: str,
    role: str = "student",
    top_k: int = 5,
    include_expired: bool = False,
) -> list[dict]:
    """通过 ChromaDB 查询相似片段，并返回统一的 RAG chunk 结构。"""
    query_embedding = embed(question)
    if not any(query_embedding):
        return []

    collection = get_collection(get_client())
    count = collection.count()
    if count == 0:
        return []

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k * 3, count),
        where=build_where(role, include_expired),
        include=["documents", "metadatas", "distances"],
    )

    items = []
    for chunk_id, text, metadata, distance in zip(
        result["ids"][0],
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    ):
        score = round(1.0 - distance, 4)
        if score <= 0:
            continue
        items.append({
            "chunk_id": chunk_id,
            "text": text,
            "metadata": metadata,
            "score": score,
            "expired": bool(metadata["expired"]),
        })

    items.sort(key=lambda x: (x["expired"], -x["score"]))
    return items[:top_k]


if __name__ == "__main__":
    print_student_id()
    build_chroma_store()
