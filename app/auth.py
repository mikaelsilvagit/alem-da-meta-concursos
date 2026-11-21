"""
Além da Meta Concursos - Autenticação Segura Multi-Usuário (PBKDF2 + Cookie HMAC).
Zero dependências externas além da biblioteca padrão Python + FastAPI.
"""

import os
import hmac
import json
import time
import base64
import hashlib
import secrets
from typing import Optional
from fastapi import Request, HTTPException
from app.database import get_db

COOKIE_NAME = "alem_da_meta_session"
SESSION_TTL_SECONDS = 60 * 60 * 24 * 30  # 30 dias

_cached_secret: Optional[str] = None


def get_secret_key() -> str:
    global _cached_secret
    env_key = os.environ.get("APP_SECRET_KEY", "").strip()
    if env_key:
        return env_key
    if _cached_secret:
        return _cached_secret

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT value FROM system_metadata WHERE key = 'auth_secret_key'")
        row = cur.fetchone()
        if row and row["value"]:
            _cached_secret = row["value"]
            return _cached_secret
        new_secret = secrets.token_hex(32)
        cur.execute(
            "INSERT INTO system_metadata (key, value) VALUES ('auth_secret_key', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (new_secret,),
        )
        _cached_secret = new_secret
        return _cached_secret


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000)
    return f"pbkdf2_sha256$200000${salt}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algo, iters_str, salt, expected_hex = stored_hash.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iters_str))
        return hmac.compare_digest(dk.hex(), expected_hex)
    except Exception:
        return False


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64d(s: str) -> bytes:
    pad = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + pad)


def create_session_token(user_id: int, username: str) -> str:
    payload = {
        "uid": int(user_id),
        "usr": username,
        "exp": int(time.time()) + SESSION_TTL_SECONDS,
    }
    payload_b64 = _b64e(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig = hmac.new(get_secret_key().encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest()
    return f"{payload_b64}.{_b64e(sig)}"


def verify_session_token(token: str) -> Optional[dict]:
    if not token or "." not in token:
        return None
    try:
        payload_b64, sig_b64 = token.split(".", 1)
        expected_sig = hmac.new(get_secret_key().encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64e(expected_sig), sig_b64):
            return None
        payload = json.loads(_b64d(payload_b64).decode("utf-8"))
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except Exception:
        return None


def get_current_user(request: Request) -> Optional[dict]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        auth_hdr = request.headers.get("Authorization", "")
        if auth_hdr.lower().startswith("bearer "):
            token = auth_hdr[7:].strip()
    if not token:
        return None
    payload = verify_session_token(token)
    if not payload:
        return None
    uid = payload.get("uid")
    if not uid:
        return None
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, username, email, display_name, is_admin, created_at FROM users WHERE id = ?", (uid,))
        row = cur.fetchone()
        return dict(row) if row else None


def require_user(request: Request) -> dict:
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Sessão expirada ou não autenticada. Faça login para continuar.")
    return user
