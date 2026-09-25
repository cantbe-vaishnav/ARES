from typing import Iterable
import ollama
from ..config import settings


client = ollama.Client(host=settings.ollama_host)


def embed_texts(texts: Iterable[str]) -> list[list[float]]:
    items = list(texts)
    if not items:
        return []

    # Newer Ollama Python clients support batched `embed`.
    try:
        response = client.embed(model=settings.embed_model, input=items)
        embeddings = response.get("embeddings") if isinstance(response, dict) else response.embeddings
        return [list(v) for v in embeddings]
    except Exception:
        # Compatibility path for older clients exposing `embeddings` per prompt.
        vectors = []
        for text in items:
            response = client.embeddings(model=settings.embed_model, prompt=text)
            vector = response.get("embedding") if isinstance(response, dict) else response.embedding
            vectors.append(list(vector))
        return vectors


def chat(system_prompt: str, user_prompt: str) -> str:
    response = client.chat(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={"temperature": 0.1},
    )
    if isinstance(response, dict):
        return response["message"]["content"].strip()
    return response.message.content.strip()
