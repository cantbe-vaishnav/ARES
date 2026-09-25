import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.auth import hash_password
from app.db import get_conn, init_db, utc_now


def main():
    init_db()
    username = input("Admin username: ").strip()
    password = getpass.getpass("Admin password: ")
    if len(username) < 3 or len(password) < 6:
        raise SystemExit("Username must be at least 3 characters and password at least 6 characters.")
    with get_conn() as conn:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            raise SystemExit("That username already exists.")
        conn.execute(
            "INSERT INTO users(username, password_hash, role, created_at) VALUES(?,?,?,?)",
            (username, hash_password(password), "admin", utc_now()),
        )
    print(f"Admin '{username}' created.")


if __name__ == "__main__":
    main()
