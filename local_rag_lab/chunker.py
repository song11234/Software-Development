# 学号：2410331105
from pathlib import Path


def load_text(path: str) -> str:
    """读取原始资料文本，作为后续切分的输入。"""
    return Path(path).read_text(encoding="utf-8")


def split_by_lines(text: str) -> list[dict]:
    """按行切分教学资料，并为每个片段生成可追溯的 id。"""
    chunks = []
    for i, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        chunks.append({
            "id": f"chunk_{i:03d}",
            "text": line,
            "source": "genshin_notes.txt",
        })
    return chunks
