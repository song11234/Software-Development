"""文件型文档存储 —— JSON 索引 + 独立文档文件。

对应知识点：第03章 RAG 知识库存储、第10章轻量级交付（零数据库依赖）。
"""
import json
import os
from datetime import datetime, timezone
from typing import Optional


class DocumentStore:
    """基于文件系统的轻量文档库。

    结构:
        data/documents/
        ├── index.json        # 索引：{doc_id: {title, category, tags, created_at}}
        ├── {doc_id}.json     # 文档正文
    """

    def __init__(self, base_dir: str = "./data/documents"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        self._index_path = os.path.join(base_dir, "index.json")
        self._index: dict[str, dict] = self._load_index()

    # ── 索引持久化 ──

    def _load_index(self) -> dict[str, dict]:
        if os.path.exists(self._index_path):
            with open(self._index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_index(self) -> None:
        with open(self._index_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, ensure_ascii=False, indent=2)

    def _doc_path(self, doc_id: str) -> str:
        return os.path.join(self.base_dir, f"{doc_id}.json")

    # ── CRUD ──

    def save(self, doc_id: str, doc: dict) -> None:
        """保存文档并更新索引。"""
        filepath = self._doc_path(doc_id)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        self._index[doc_id] = {
            "title": doc.get("title", ""),
            "category": doc.get("category", ""),
            "tags": doc.get("tags", []),
            "created_at": doc.get("created_at", datetime.now(timezone.utc).isoformat()),
        }
        self._save_index()

    def get(self, doc_id: str) -> Optional[dict]:
        """按 ID 获取文档。"""
        filepath = self._doc_path(doc_id)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def list_all(
        self,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        """分页列出文档，支持按分类过滤。"""
        docs = []
        for doc_id, meta in self._index.items():
            if category and meta.get("category") != category:
                continue
            docs.append({"document_id": doc_id, **meta})

        docs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        total = len(docs)
        start = (page - 1) * page_size
        return docs[start:start + page_size], total

    def search(self, query: str, category: Optional[str] = None, top_k: int = 5) -> list[dict]:
        """关键词检索，按标题 > 摘要 > 标签 > 正文 加权打分。

        对应知识点：第03章 RAG 检索策略、第08章成本控制（不依赖 embedding API）。
        """
        results = []
        query_lower = query.lower()

        for doc_id in self._index:
            if category and self._index[doc_id].get("category") != category:
                continue

            doc = self.get(doc_id)
            if doc is None:
                continue

            score = 0.0
            if query_lower in doc.get("title", "").lower():
                score += 5.0
            if query_lower in doc.get("summary", "").lower():
                score += 3.0
            for tag in doc.get("tags", []):
                if query_lower in tag.lower():
                    score += 2.0
            if query_lower in doc.get("content", "").lower():
                score += 1.0
            # 部分匹配加分
            for word in query_lower.split():
                if word in doc.get("title", "").lower():
                    score += 1.0
                if word in " ".join(doc.get("tags", [])).lower():
                    score += 0.5

            if score > 0:
                results.append({
                    "document_id": doc_id,
                    "title": doc.get("title", ""),
                    "category": doc.get("category", ""),
                    "summary": doc.get("summary", ""),
                    "relevance_score": round(score, 2),
                })

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:top_k]

    def delete(self, doc_id: str) -> bool:
        """删除文档及索引条目。"""
        filepath = self._doc_path(doc_id)
        if os.path.exists(filepath):
            os.remove(filepath)
        if doc_id in self._index:
            del self._index[doc_id]
            self._save_index()
            return True
        return False

    def count(self) -> int:
        return len(self._index)
