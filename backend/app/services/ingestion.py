from pathlib import Path
from typing import Iterable
import fitz
import pandas as pd


SUPPORTED_EXTENSIONS = {".pdf", ".csv", ".xlsx", ".xls"}


def chunk_text(text: str, chunk_size: int = 3500, overlap: int = 400) -> list[str]:
    cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if not cleaned:
        return []
    chunks = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + chunk_size)
        piece = cleaned[start:end]
        if end < len(cleaned):
            split = max(piece.rfind("\n"), piece.rfind(". "))
            if split > chunk_size * 0.55:
                end = start + split + 1
                piece = cleaned[start:end]
        chunks.append(piece.strip())
        if end >= len(cleaned):
            break
        start = max(start + 1, end - overlap)
    return [c for c in chunks if c]


def pdf_chunks(path: Path) -> list[dict]:
    output = []
    with fitz.open(path) as doc:
        for page_index, page in enumerate(doc):
            text = page.get_text("text") or ""
            for local_index, chunk in enumerate(chunk_text(text)):
                output.append({"text": chunk, "page": page_index + 1, "part": local_index + 1})
    return output


def dataframe_to_chunks(df: pd.DataFrame, sheet: str | None = None) -> list[dict]:
    df = df.fillna("")
    lines = []
    headers = [str(c) for c in df.columns]
    for idx, row in df.iterrows():
        values = [f"{headers[i]}: {row.iloc[i]}" for i in range(len(headers)) if str(row.iloc[i]).strip()]
        if values:
            lines.append(f"Row {idx + 1}: " + " | ".join(values))
    prefix = f"Sheet: {sheet}\n" if sheet else ""
    chunks = []
    for i, chunk in enumerate(chunk_text(prefix + "\n".join(lines))):
        chunks.append({"text": chunk, "page": None, "part": i + 1, "sheet": sheet})
    return chunks


def tabular_chunks(path: Path) -> list[dict]:
    if path.suffix.lower() == ".csv":
        return dataframe_to_chunks(pd.read_csv(path))
    sheets = pd.read_excel(path, sheet_name=None)
    output = []
    for sheet_name, df in sheets.items():
        output.extend(dataframe_to_chunks(df, sheet_name))
    return output


def extract_chunks(path: Path) -> list[dict]:
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")
    if ext == ".pdf":
        return pdf_chunks(path)
    return tabular_chunks(path)
