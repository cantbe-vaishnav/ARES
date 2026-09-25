from fastapi import APIRouter, Depends, HTTPException
from ..deps import admin_user
from ..schemas import UserCreate, RoleUpdate
from ..auth import hash_password
from ..db import get_conn, utc_now

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def users(_: dict = Depends(admin_user)):
    with get_conn() as conn:
        rows = conn.execute("SELECT id, username, role, created_at FROM users ORDER BY id").fetchall()
    return [dict(r) for r in rows]


@router.post("/users")
def create_user(body: UserCreate, _: dict = Depends(admin_user)):
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO users(username, password_hash, role, created_at) VALUES(?,?,?,?)",
                (body.username.strip(), hash_password(body.password), body.role, utc_now()),
            )
            user_id = cur.lastrowid
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Username already exists or is invalid") from exc
    return {"id": user_id, "username": body.username.strip(), "role": body.role}


@router.patch("/users/{user_id}/role")
def change_role(user_id: int, body: RoleUpdate, admin: dict = Depends(admin_user)):
    if user_id == admin["id"] and body.role != "admin":
        raise HTTPException(status_code=400, detail="You cannot remove your own admin role")
    with get_conn() as conn:
        cur = conn.execute("UPDATE users SET role = ? WHERE id = ?", (body.role, user_id))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
    return {"ok": True}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, admin: dict = Depends(admin_user)):
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
    return {"ok": True}
