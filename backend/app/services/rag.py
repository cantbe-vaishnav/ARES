import re
import time
from dataclasses import dataclass
from ..config import settings
from ..db import get_conn
from .ollama_client import chat
from .vector_store import search_file


SYSTEM_PROMPT = """You are ARES, a private local document assistant.
Answer strictly from the supplied document context. Do not invent facts.
If the context is insufficient, clearly say that the answer is not available in this file.
Keep numerical values and units exact. When useful, mention the page or sheet supplied in the context metadata.
"""


@dataclass
class CacheEntry:
    expires_at: float
    value: dict


_CACHE: dict[str, CacheEntry] = {}


def _cache_key(query: str, file_ids: list[int]) -> str:
    return f"{query.strip().lower()}|{','.join(map(str, sorted(file_ids)))}"


def _get_cache(key: str):
    item = _CACHE.get(key)
    if not item:
        return None
    if item.expires_at < time.time():
        _CACHE.pop(key, None)
        return None
    return item.value


def _set_cache(key: str, value: dict):
    _CACHE[key] = CacheEntry(time.time() + settings.cache_ttl_seconds, value)


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(t) > 2}


def route_documents(query: str, documents: list[dict]) -> list[dict]:
    q = _tokens(query)
    scored = []
    for doc in documents:
        name_tokens = _tokens(doc["filename"].replace("_", " ").replace("-", " "))
        overlap = len(q & name_tokens)
        contains = sum(1 for token in q if token in doc["filename"].lower())
        score = overlap * 3 + contains
        scored.append((score, doc))
    scored.sort(key=lambda x: (x[0], x[1]["created_at"]), reverse=True)
    positive = [doc for score, doc in scored if score > 0]
    if positive:
        return positive[: settings.max_routed_files]
    return [doc for _, doc in scored[: settings.max_routed_files]]


def _context_for_chunks(chunks: list[dict]) -> str:
    blocks = []
    for i, item in enumerate(chunks, 1):
        meta = item["metadata"] or {}
        loc = []
        if meta.get("page"):
            loc.append(f"page {meta['page']}")
        if meta.get("sheet"):
            loc.append(f"sheet {meta['sheet']}")
        where = f" ({', '.join(loc)})" if loc else ""
        blocks.append(f"[Chunk {i}{where}]\n{item['text']}")
    return "\n\n".join(blocks)


def answer_query(query: str, selected_file_ids: list[int]) -> dict:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
    documents = [dict(r) for r in rows]
    if not documents:
        return {"answer": "No documents are indexed yet.", "files": [], "routed_file_ids": []}

    if selected_file_ids:
        chosen = [d for d in documents if d["id"] in set(selected_file_ids)]
    else:
        chosen = route_documents(query, documents)

    if not chosen:
        return {"answer": "None of the selected documents are available.", "files": [], "routed_file_ids": []}

    chosen_ids = [d["id"] for d in chosen]
    key = _cache_key(query, chosen_ids)
    cached = _get_cache(key)
    if cached:
        return cached

    file_results = []
    formatted_sections = []
    for doc in chosen:
        chunks = search_file(doc["id"], query, settings.top_k)
        context = _context_for_chunks(chunks)
        prompt = f"""Document: {doc['filename']}

Question:
{query}

Retrieved context:
{context or '[No matching text retrieved]'}

Return a concise, evidence-grounded answer for this document only."""
        answer = chat(SYSTEM_PROMPT, prompt) if chunks else "No relevant text was retrieved from this file."
        sources = [
            {
                "page": c["metadata"].get("page"),
                "sheet": c["metadata"].get("sheet"),
                "chunk_index": c["metadata"].get("chunk_index"),
                "distance": c.get("distance"),
            }
            for c in chunks
        ]
        file_results.append({"file_id": doc["id"], "filename": doc["filename"], "answer": answer, "sources": sources})
        formatted_sections.append(f"## {doc['filename']}\n{answer}")

    result = {
        "answer": "\n\n".join(formatted_sections),
        "files": file_results,
        "routed_file_ids": chosen_ids,
    }
    _set_cache(key, result)
    return result
