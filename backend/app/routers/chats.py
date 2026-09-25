import json
from fastapi import APIRouter, Depends, HTTPException
from ..db import get_conn, utc_now
from ..deps import current_user
from ..schemas import ChatCreate, ChatRename, QueryRequest
from ..services.rag import answer_query

router = APIRouter(prefix="/chats", tags=["chats"])


def owned_chat(chat_id: int, user_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM chats WHERE id = ? AND user_id = ?", (chat_id, user_id)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Chat not found")
    return dict(row)


@router.get("")
def list_chats(user: dict = Depends(current_user)):
    with get_conn() as conn:
        rows = conn.execute("SELECT id, title, created_at, updated_at FROM chats WHERE user_id = ? ORDER BY updated_at DESC", (user["id"],)).fetchall()
    return [dict(r) for r in rows]


@router.post("")
def create_chat(body: ChatCreate, user: dict = Depends(current_user)):
    now = utc_now()
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO chats(user_id, title, created_at, updated_at) VALUES(?,?,?,?)", (user["id"], body.title.strip() or "New Chat", now, now))
        chat_id = cur.lastrowid
    return {"id": chat_id, "title": body.title.strip() or "New Chat", "created_at": now, "updated_at": now}


@router.patch("/{chat_id}")
def rename_chat(chat_id: int, body: ChatRename, user: dict = Depends(current_user)):
    owned_chat(chat_id, user["id"])
    with get_conn() as conn:
        conn.execute("UPDATE chats SET title = ?, updated_at = ? WHERE id = ?", (body.title.strip(), utc_now(), chat_id))
    return {"ok": True}


@router.delete("/{chat_id}")
def delete_chat(chat_id: int, user: dict = Depends(current_user)):
    owned_chat(chat_id, user["id"])
    with get_conn() as conn:
        conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    return {"ok": True}


@router.get("/{chat_id}/messages")
def get_messages(chat_id: int, user: dict = Depends(current_user)):
    owned_chat(chat_id, user["id"])
    with get_conn() as conn:
        rows = conn.execute("SELECT id, role, content, sources_json, created_at FROM messages WHERE chat_id = ? ORDER BY id", (chat_id,)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["sources"] = json.loads(item.pop("sources_json") or "null")
        result.append(item)
    return result


@router.post("/{chat_id}/query")
def query_chat(chat_id: int, body: QueryRequest, user: dict = Depends(current_user)):
    owned_chat(chat_id, user["id"])
    now = utc_now()
    with get_conn() as conn:
        conn.execute("INSERT INTO messages(chat_id, role, content, created_at) VALUES(?,?,?,?)", (chat_id, "user", body.query.strip(), now))

    result = answer_query(body.query.strip(), body.selected_file_ids)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages(chat_id, role, content, sources_json, created_at) VALUES(?,?,?,?,?)",
            (chat_id, "assistant", result["answer"], json.dumps(result), utc_now()),
        )
        current = conn.execute("SELECT title FROM chats WHERE id = ?", (chat_id,)).fetchone()
        if current and current["title"] == "New Chat":
            auto_title = body.query.strip()[:60] or "New Chat"
            conn.execute("UPDATE chats SET title = ?, updated_at = ? WHERE id = ?", (auto_title, utc_now(), chat_id))
        else:
            conn.execute("UPDATE chats SET updated_at = ? WHERE id = ?", (utc_now(), chat_id))
    return result
