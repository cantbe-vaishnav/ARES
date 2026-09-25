from fastapi import APIRouter, HTTPException, status, Depends
from ..schemas import LoginRequest
from ..auth import verify_password, create_token
from ..db import get_conn
from ..deps import current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(body: LoginRequest):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (body.username.strip(),)).fetchone()
    if not row or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    token = create_token(row["id"], row["username"], row["role"])
    return {"access_token": token, "token_type": "bearer", "user": {"id": row["id"], "username": row["username"], "role": row["role"]}}


@router.get("/me")
def me(user: dict = Depends(current_user)):
    return user
