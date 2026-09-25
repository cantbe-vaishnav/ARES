from typing import Any
import chromadb
from ..config import settings
from .ollama_client import embed_texts


_client = chromadb.PersistentClient(path=str(settings.chroma_dir))
_collection = _client.get_or_create_collection(name="ares_documents", metadata={"hnsw:space": "cosine"})


def add_chunks(file_id: int, filename: str, chunks: list[dict]) -> int:
    if not chunks:
        return 0
    ids = [f"{file_id}:{i}" for i in range(len(chunks))]
    documents = [c["text"] for c in chunks]
    metadatas = []
    for i, c in enumerate(chunks):
        metadata: dict[str, Any] = {
            "file_id": int(file_id),
            "filename": filename,
            "chunk_index": int(i),
            "part": int(c.get("part") or i + 1),
        }
        if c.get("page") is not None:
            metadata["page"] = int(c["page"])
        if c.get("sheet"):
            metadata["sheet"] = str(c["sheet"])
        metadatas.append(metadata)

    batch_size = max(1, min(settings.chroma_batch_size, 1000))
    for start in range(0, len(documents), batch_size):
        end = start + batch_size
        batch_docs = documents[start:end]
        batch_embeddings = embed_texts(batch_docs)
        _collection.add(
            ids=ids[start:end],
            documents=batch_docs,
            metadatas=metadatas[start:end],
            embeddings=batch_embeddings,
        )
    return len(documents)


def delete_file(file_id: int):
    _collection.delete(where={"file_id": int(file_id)})


def search_file(file_id: int, query: str, top_k: int) -> list[dict]:
    q_embedding = embed_texts([query])[0]
    result = _collection.query(
        query_embeddings=[q_embedding],
        n_results=max(1, top_k),
        where={"file_id": int(file_id)},
        include=["documents", "metadatas", "distances"],
    )
    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    rows = []
    for document, metadata, distance in zip(docs, metas, distances):
        rows.append({"text": document, "metadata": metadata, "distance": distance})
    return rows
