import json
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from ..deps import current_user, admin_user
from ..db import get_conn, utc_now
from ..config import settings
from ..services.ingestion import SUPPORTED_EXTENSIONS, extract_chunks
from ..services.vector_store import add_chunks, delete_file

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def list_documents(_: dict = Depends(current_user)):
    with get_conn() as conn:
        rows = conn.execute("SELECT id, filename, file_type, chunk_count, created_at FROM documents ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), _: dict = Depends(admin_user)):
    original_name = Path(file.filename or "upload").name
    ext = Path(original_name).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported type. Allowed: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")

    stored_name = f"{uuid.uuid4().hex}{ext}"
    path = settings.uploads_dir / stored_name
    data = await file.read()
    path.write_bytes(data)

    try:
        chunks = extract_chunks(path)
        if not chunks:
            raise ValueError("No readable text/data found in the uploaded file")
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO documents(filename, stored_name, file_type, chunk_count, created_at) VALUES(?,?,?,?,?)",
                (original_name, stored_name, ext.lstrip("."), 0, utc_now()),
            )
            file_id = cur.lastrowid
        try:
            count = add_chunks(file_id, original_name, chunks)
            with get_conn() as conn:
                conn.execute("UPDATE documents SET chunk_count = ? WHERE id = ?", (count, file_id))
        except Exception:
            delete_file(file_id)
            with get_conn() as conn:
                conn.execute("DELETE FROM documents WHERE id = ?", (file_id,))
            raise
        return {"id": file_id, "filename": original_name, "chunk_count": count}
    except Exception as exc:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{file_id}")
def remove_document(file_id: int, _: dict = Depends(admin_user)):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (file_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    delete_file(file_id)
    (settings.uploads_dir / row["stored_name"]).unlink(missing_ok=True)
    with get_conn() as conn:
        conn.execute("DELETE FROM documents WHERE id = ?", (file_id,))
    return {"ok": True}
