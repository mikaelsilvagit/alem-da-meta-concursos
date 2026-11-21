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
import threading
from collections import defaultdict
from typing import Optional
from fastapi import Request, HTTPException
from app.database import get_db

COOKIE_NAME = "alem_da_meta_session"
SESSION_TTL_SECONDS = 60 * 60 * 24 * 30  # 30 dias

# Rate limiting em memória (thread-safe) para proteção contra força bruta e spam
_rate_lock = threading.Lock()
_login_failures: dict = defaultdict(list)
_register_attempts: dict = defaultdict(list)

LOGIN_MAX_ATTEMPTS = 8
LOGIN_WINDOW_SECONDS = 300      # 5 minutos
REGISTER_MAX_ATTEMPTS = 5
REGISTER_WINDOW_SECONDS = 900   # 15 minutos


def get_client_ip(request: Request) -> str:
    xff = request.headers.get("X-Forwarded-For", "").strip()
    if xff:
        return xff.split(",")[0].strip()
    xri = request.headers.get("X-Real-IP", "").strip()
    if xri:
        return xri
    return request.client.host if request.client else "unknown"


def check_login_rate_limit(ip: str):
    now = time.time()
    with _rate_lock:
        recent = [t for t in _login_failures[ip] if now - t < LOGIN_WINDOW_SECONDS]
        _login_failures[ip] = recent
        if len(recent) >= LOGIN_MAX_ATTEMPTS:
            wait_min = max(1, int((LOGIN_WINDOW_SECONDS - (now - recent[0])) // 60) + 1)
            raise HTTPException(
                status_code=429,
                detail=f"Muitas tentativas de login incorretas. Aguarde cerca de {wait_min} minuto(s) para tentar novamente.",
            )


def record_login_failure(ip: str):
    now = time.time()
    with _rate_lock:
        recent = [t for t in _login_failures[ip] if now - t < LOGIN_WINDOW_SECONDS]
        recent.append(now)
        _login_failures[ip] = recent


def clear_login_failures(ip: str):
    with _rate_lock:
        _login_failures.pop(ip, None)


def check_register_rate_limit(ip: str):
    now = time.time()
    with _rate_lock:
        recent = [t for t in _register_attempts[ip] if now - t < REGISTER_WINDOW_SECONDS]
        if len(recent) >= REGISTER_MAX_ATTEMPTS:
            raise HTTPException(
                status_code=429,
                detail="Limite temporário de criação de contas atingido para este IP. Aguarde alguns minutos.",
            )
        recent.append(now)
        _register_attempts[ip] = recent

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
