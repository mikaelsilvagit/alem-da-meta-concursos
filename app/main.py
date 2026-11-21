import os
import sys
import socket
import datetime
import csv
import io
import json
import re
import unicodedata
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel
from typing import Optional, List

from app.database import init_db, enable_wal, get_db, is_system_seeded, mark_system_seeded
from app.seed_data import seed_initial_data, seed_platforms, seed_tactical_expansions
from app.news_service import sync_estrategia_news
from app.auth import (
    COOKIE_NAME, SESSION_TTL_SECONDS, hash_password, verify_password,
    create_session_token, get_current_user, require_user
)
from app.career_templates import CAREER_TEMPLATES, DEFAULT_PLATFORMS

# Allow importing root backup_manager for automatic startup backup (B1)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
try:
    from backup_manager import auto_backup_db
except Exception:
    auto_backup_db = None

app = FastAPI(title="Além da Meta Concursos - Centro de Operações de Estudos", version="3.0.0")

BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Disable browser caching in development to ensure JS/CSS changes apply immediately
@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Initialize DB and preserve user data on startup
@app.on_event("startup")
def on_startup():
    enable_wal()
    init_db()
    if not is_system_seeded():
        print("🌱 Executando carga inicial de dados (primeira execução)...")
        seed_initial_data()
        seed_platforms()
        seed_tactical_expansions()
        mark_system_seeded()
        print("✓ Carga inicial concluída com sucesso.")
    else:
        print("🛡️ Além da Meta Concursos v3.0 - Multi-Usuário ativo (WAL + índices + dados preservados).")
    # Garantir que sempre exista ao menos 1 administrador (primeiro usuário cadastrado ou ADMIN_USERNAME)
    with get_db() as conn:
        cur = conn.cursor()
        admin_uname = os.environ.get("ADMIN_USERNAME", "").strip().lower()
        if admin_uname:
            cur.execute("UPDATE users SET is_admin = 1 WHERE LOWER(username) = ?", (admin_uname,))
        cur.execute("SELECT COUNT(*) as cnt FROM users WHERE is_admin = 1")
        if cur.fetchone()["cnt"] == 0:
            cur.execute("UPDATE users SET is_admin = 1 WHERE id = (SELECT id FROM users ORDER BY id ASC LIMIT 1)")
    if auto_backup_db:
        bkp = auto_backup_db(max_keep=10)
        if bkp:
            print(f"💾 Backup automático criado: {os.path.basename(bkp)} (mantendo os 10 últimos).")

def format_seconds_hm(total_seconds: int) -> str:
    sec = max(0, int(total_seconds or 0))
    total_mins = round(sec / 60)
    hrs = total_mins // 60
    rem_m = total_mins % 60
    if hrs > 0:
        return f"{hrs}h {rem_m:02d}m"
    return f"{rem_m}m" if rem_m > 0 else "0h 00m"

# Helper: Compute Rank & XP based on total study seconds (exact h/m formatting)
def get_rank_info(total_seconds: int):
    total_hours = (total_seconds or 0) / 3600.0
    ranks = [
        {"threshold": 0, "title": "Recruta Operacional", "level": 1, "badge": "fa-user-shield", "next_at": 10},
        {"threshold": 10, "title": "Soldado 2ª Classe", "level": 2, "badge": "fa-shield", "next_at": 30},
        {"threshold": 30, "title": "Soldado 1ª Classe", "level": 3, "badge": "fa-shield-halved", "next_at": 60},
        {"threshold": 60, "title": "Cabo Tático", "level": 4, "badge": "fa-chevron-down", "next_at": 100},
        {"threshold": 100, "title": "3º Sargento", "level": 5, "badge": "fa-angles-down", "next_at": 160},
        {"threshold": 160, "title": "2º Sargento", "level": 6, "badge": "fa-medal", "next_at": 240},
        {"threshold": 240, "title": "1º Sargento", "level": 7, "badge": "fa-award", "next_at": 350},
        {"threshold": 350, "title": "Subtenente / Inspetor", "level": 8, "badge": "fa-id-badge", "next_at": 500},
        {"threshold": 500, "title": "Tenente Operacional", "level": 9, "badge": "fa-star", "next_at": 700},
        {"threshold": 700, "title": "Capitão Tático", "level": 10, "badge": "fa-certificate", "next_at": 950},
        {"threshold": 950, "title": "Major Comandante", "level": 11, "badge": "fa-crosshairs", "next_at": 1300},
        {"threshold": 1300, "title": "Coronel de Operações", "level": 12, "badge": "fa-crown", "next_at": 1800},
        {"threshold": 1800, "title": "Delegado Geral / Lenda Policial", "level": 13, "badge": "fa-shield-heart", "next_at": 2500},
    ]
    current_rank = ranks[0]
    for r in ranks:
        if total_hours >= r["threshold"]:
            current_rank = r
        else:
            break
            
    prev_threshold = current_rank["threshold"]
    next_threshold = current_rank["next_at"]
    hours_in_rank = max(0.0, total_hours - prev_threshold)
    span = max(1.0, next_threshold - prev_threshold)
    progress_pct = min(100.0, round((hours_in_rank / span) * 100, 1))
    needed_seconds = max(0, int(next_threshold * 3600) - int(total_seconds or 0))

    return {
        "title": current_rank["title"],
        "level": current_rank["level"],
        "badge": current_rank["badge"],
        "total_hours": round(total_hours, 1),
        "total_formatted": format_seconds_hm(total_seconds),
        "next_threshold": next_threshold,
        "hours_needed": round(max(0.0, next_threshold - total_hours), 1),
        "needed_seconds": needed_seconds,
        "needed_formatted": format_seconds_hm(needed_seconds),
        "progress_pct": progress_pct
    }

# ==================== MAIN PAGE & AUTHENTICATION ====================
@app.get("/", response_class=HTMLResponse)
def serve_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Alem da Meta Concursos", "version": "3.0.0"}


class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str
    email: Optional[str] = ""
    career_key: str = "PM"
    target_role: Optional[str] = ""
    daily_goal_minutes: int = 180
    weekly_goal_hours: int = 20


class LoginRequest(BaseModel):
    username: str
    password: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class ApplyCareerTemplateRequest(BaseModel):
    career_key: str
    target_role: Optional[str] = ""
    mode: str = "merge"  # merge | replace_unused


def _populate_user_career(cursor, user_id: int, career_key: str, target_role: str = "", mode: str = "merge"):
    tpl = CAREER_TEMPLATES.get(career_key.upper(), CAREER_TEMPLATES["CUSTOM"])
    final_role = (target_role or "").strip() or tpl["default_role"]

    cursor.execute("SELECT id, name FROM subjects WHERE user_id = ?", (user_id,))
    existing_map = {r["name"].strip().lower(): r["id"] for r in cursor.fetchall()}
    kept_ids = set()

    for s in tpl["subjects"]:
        key = s["name"].strip().lower()
        if key in existing_map:
            subj_id = existing_map[key]
            cursor.execute("UPDATE subjects SET weight = ?, target_hours = ? WHERE id = ?", (s["weight"], s["target_hours"], subj_id))
        else:
            cursor.execute("""
            INSERT INTO subjects (user_id, name, category, color, icon, target_hours, weight)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, s["name"], s["category"], s["color"], s["icon"], s["target_hours"], s["weight"]))
            subj_id = cursor.lastrowid
        kept_ids.add(subj_id)

        cursor.execute("SELECT name FROM topics WHERE subject_id = ?", (subj_id,))
        existing_topics = {r["name"].strip().lower() for r in cursor.fetchall()}
        for t_name in s["topics"]:
            if t_name.strip().lower() not in existing_topics:
                cursor.execute("INSERT INTO topics (subject_id, name) VALUES (?, ?)", (subj_id, t_name))

    if mode == "replace_unused" and kept_ids:
        cursor.execute("""
        SELECT s.id FROM subjects s
        LEFT JOIN study_sessions ss ON ss.subject_id = s.id AND ss.user_id = ?
        WHERE s.user_id = ?
        GROUP BY s.id
        HAVING COALESCE(SUM(ss.duration_seconds), 0) = 0
        """, (user_id, user_id))
        for r in cursor.fetchall():
            if r["id"] not in kept_ids:
                cursor.execute("DELETE FROM subjects WHERE id = ? AND user_id = ?", (r["id"], user_id))

    cursor.execute("UPDATE user_profile SET target_role = ? WHERE user_id = ?", (final_role, user_id))
    return final_role


@app.get("/api/auth/careers")
def list_career_templates():
    return [
        {"key": k, "label": v["label"], "default_role": v["default_role"], "subjects_count": len(v["subjects"])}
        for k, v in CAREER_TEMPLATES.items()
    ]


@app.get("/api/auth/me")
def auth_me(request: Request):
    user = get_current_user(request)
    if not user:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": user}


@app.post("/api/auth/register")
def auth_register(data: RegisterRequest, response: Response):
    uname = re.sub(r"[^a-zA-Z0-9_.-]", "", (data.username or "").strip().lower())
    if len(uname) < 3:
        raise HTTPException(status_code=400, detail="O nome de usuário deve ter pelo menos 3 caracteres (letras/números).")
    if len(data.password or "") < 4:
        raise HTTPException(status_code=400, detail="A senha deve ter pelo menos 4 caracteres.")
    disp = (data.display_name or "").strip() or uname

    tpl = CAREER_TEMPLATES.get((data.career_key or "PM").upper(), CAREER_TEMPLATES["CUSTOM"])
    target_role = (data.target_role or "").strip() or tpl["default_role"]
    pwd_hash = hash_password(data.password)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (uname,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Este nome de usuário já está em uso. Escolha outro.")

        cursor.execute("SELECT COUNT(*) as cnt FROM users")
        is_first_user = 1 if cursor.fetchone()["cnt"] == 0 else 0

        cursor.execute("""
        INSERT INTO users (username, email, display_name, password_hash, is_admin)
        VALUES (?, ?, ?, ?, ?)
        """, (uname, (data.email or "").strip(), disp, pwd_hash, is_first_user))
        uid = cursor.lastrowid

        cursor.execute("""
        INSERT INTO user_profile (user_id, name, target_role, daily_goal_minutes, weekly_goal_hours, sound_enabled)
        VALUES (?, ?, ?, ?, ?, 1)
        """, (uid, disp, target_role, max(30, min(720, data.daily_goal_minutes)), max(5, min(100, data.weekly_goal_hours))))

        _populate_user_career(cursor, uid, data.career_key, target_role, mode="merge")

        for title, url, cat, icon, color, notes, pin in DEFAULT_PLATFORMS:
            cursor.execute("""
            INSERT INTO study_platforms (user_id, title, url, category, icon, color, notes, is_pinned)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (uid, title, url, cat, icon, color, notes, pin))

        target_date = (datetime.date.today() + datetime.timedelta(days=90)).strftime("%Y-%m-%d")
        cursor.execute("""
        INSERT INTO exam_countdowns (user_id, title, target_date, target_time, is_active)
        VALUES (?, ?, ?, '08:00', 1)
        """, (uid, tpl["countdown_title"], target_date))

    token = create_session_token(uid, uname)
    is_https = os.environ.get("COOKIE_SECURE", "").lower() == "true"
    response.set_cookie(
        key=COOKIE_NAME, value=token, httponly=True, max_age=SESSION_TTL_SECONDS,
        samesite="lax", secure=is_https, path="/"
    )
    return {
        "authenticated": True,
        "user": {"id": uid, "username": uname, "display_name": disp, "is_admin": is_first_user},
        "message": f"Conta criada! Trilha '{tpl['label']}' configurada para você."
    }


@app.post("/api/auth/login")
def auth_login(data: LoginRequest, response: Response):
    ident = (data.username or "").strip().lower()
    if not ident or not data.password:
        raise HTTPException(status_code=400, detail="Informe usuário e senha.")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(username) = ? OR (email != '' AND LOWER(email) = ?)", (ident, ident))
        user = cursor.fetchone()
        if not user or not verify_password(data.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Usuário ou senha inválidos.")

    token = create_session_token(user["id"], user["username"])
    is_https = os.environ.get("COOKIE_SECURE", "").lower() == "true"
    response.set_cookie(
        key=COOKIE_NAME, value=token, httponly=True, max_age=SESSION_TTL_SECONDS,
        samesite="lax", secure=is_https, path="/"
    )
    return {
        "authenticated": True,
        "user": {"id": user["id"], "username": user["username"], "display_name": user["display_name"], "is_admin": user["is_admin"]},
        "message": f"Bem-vindo(a), {user['display_name']}!"
    }


@app.post("/api/auth/logout")
def auth_logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"authenticated": False, "message": "Sessão encerrada com segurança."}


@app.put("/api/auth/password")
def auth_change_password(data: PasswordChangeRequest, request: Request):
    user = require_user(request)
    if len(data.new_password or "") < 4:
        raise HTTPException(status_code=400, detail="A nova senha deve ter pelo menos 4 caracteres.")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user["id"],))
        row = cursor.fetchone()
        if not row or not verify_password(data.current_password, row["password_hash"]):
            raise HTTPException(status_code=400, detail="Senha atual incorreta.")
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(data.new_password), user["id"]))
    return {"message": "Senha alterada com sucesso!"}


@app.post("/api/career/apply-template")
def apply_career_template(data: ApplyCareerTemplateRequest, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        final_role = _populate_user_career(cursor, user["id"], data.career_key, data.target_role or "", mode=data.mode)
    return {"success": True, "target_role": final_role, "message": f"Trilha aplicada para '{final_role}'! Suas horas estudadas foram preservadas."}


# ==================== PAINEL ADMIN (GESTÃO DE USUÁRIOS & SENHAS) ====================
class AdminPasswordResetRequest(BaseModel):
    new_password: str


def _require_admin(request: Request) -> dict:
    user = require_user(request)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Acesso restrito ao administrador do sistema.")
    return user


@app.get("/api/admin/users")
def admin_list_users(request: Request):
    _require_admin(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT u.id, u.username, u.display_name, u.email, u.is_admin, u.created_at,
               COALESCE(p.target_role, '') as target_role
        FROM users u
        LEFT JOIN user_profile p ON p.user_id = u.id
        ORDER BY u.id ASC
        """)
        return [dict(r) for r in cursor.fetchall()]


@app.post("/api/admin/users/{target_user_id}/reset-password")
def admin_reset_password(target_user_id: int, data: AdminPasswordResetRequest, request: Request):
    _require_admin(request)
    if len(data.new_password or "") < 4:
        raise HTTPException(status_code=400, detail="A nova senha provisória deve ter pelo menos 4 caracteres.")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users WHERE id = ?", (target_user_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(data.new_password), target_user_id))
    return {"success": True, "message": f"Senha provisória definida para @{row['username']}!"}

# Helper: Compute Weighted Intelligent Tactical Cycle (A1 - Next Mission)
def compute_tactical_cycle(cursor, user_id: int, return_all=False):
    cursor.execute("""
    SELECT s.id, s.name, s.color, s.icon, s.target_hours, COALESCE(s.weight, 1.0) as weight,
           COALESCE(SUM(ss.duration_seconds), 0) as total_seconds,
           MAX(ss.date) as last_study_date
    FROM subjects s
    LEFT JOIN study_sessions ss ON s.id = ss.subject_id AND ss.user_id = ?
    WHERE s.user_id = ?
    GROUP BY s.id
    ORDER BY s.id ASC
    """, (user_id, user_id))
    rows = cursor.fetchall()
    if not rows:
        return [] if return_all else None
        
    today = datetime.date.today()
    scored = []
    
    for r in rows:
        last_d_str = r["last_study_date"]
        if last_d_str:
            try:
                last_d = datetime.datetime.strptime(last_d_str, "%Y-%m-%d").date()
                days_without = max(0, (today - last_d).days)
            except Exception:
                days_without = 7
        else:
            days_without = 14
            
        hrs = r["total_seconds"] / 3600
        target = r["target_hours"] or 50.0
        pct = min(100.0, (hrs / target) * 100)
        weight = float(r["weight"] or 1.0)
        
        # Weighted Priority Score (A1): edital weight amplifies urgency of high-value subjects
        base_urgency = (min(days_without, 21) * 12.0) + max(0.0, 100.0 - pct)
        score = round(base_urgency * (0.55 + 0.45 * weight), 2)
        scored.append({
            "id": r["id"],
            "name": r["name"],
            "color": r["color"],
            "icon": r["icon"],
            "weight": weight,
            "days_without": days_without,
            "studied_hours": round(hrs, 1),
            "target_hours": target,
            "pct": round(pct, 1),
            "score": score
        })
        
    scored.sort(key=lambda x: x["score"], reverse=True)
    if return_all:
        return scored

    top = scored[0]
    
    cursor.execute("""
    SELECT id, name FROM topics 
    WHERE subject_id = ? AND (theory_completed = 0 OR summary_completed = 0 OR questions_completed = 0)
    ORDER BY id ASC LIMIT 1
    """, (top["id"],))
    topic_row = cursor.fetchone()
    suggested_topic = dict(topic_row) if topic_row else None
    
    weight_label = f"Peso {top['weight']:.1f}x no edital"
    if top["days_without"] >= 14:
        reason = f"Sem registro recente • {weight_label}"
    elif top["days_without"] > 0:
        reason = f"{top['days_without']} dias sem contato • {weight_label}"
    else:
        reason = f"Manter constância • {weight_label}"
    return {
        "subject_id": top["id"],
        "subject_name": top["name"],
        "subject_color": top["color"],
        "subject_icon": top["icon"],
        "weight": top["weight"],
        "days_without": top["days_without"],
        "studied_hours": top["studied_hours"],
        "reason": reason,
        "suggested_topic": suggested_topic,
        "queue": scored[:4]
    }


# Helper: Compute Study Streak & Consistency Alert (A3)
def compute_streak(cursor, user_id: int):
    cursor.execute("""
    SELECT DISTINCT date FROM study_sessions
    WHERE user_id = ? AND duration_seconds > 0
    ORDER BY date DESC
    """, (user_id,))
    date_strs = [r["date"] for r in cursor.fetchall() if r["date"]]
    today = datetime.date.today()

    if not date_strs:
        return {
            "current_streak": 0,
            "best_streak": 0,
            "days_since_last": None,
            "studied_today": False,
            "last_study_date": None,
            "alert_level": "danger",
            "alert_message": "Nenhum turno registrado ainda. Comece hoje para abrir sua sequência!"
        }

    parsed_dates = sorted(
        {datetime.datetime.strptime(d, "%Y-%m-%d").date() for d in date_strs},
        reverse=True
    )
    latest = parsed_dates[0]
    days_since_last = max(0, (today - latest).days)
    studied_today = (latest == today)

    # Current streak (counts backwards from today if studied today, or from yesterday if still within grace period)
    current_streak = 0
    if days_since_last <= 1:
        expected = latest
        for d in parsed_dates:
            if d == expected:
                current_streak += 1
                expected = expected - datetime.timedelta(days=1)
            else:
                break

    # Best streak ever
    asc_dates = sorted(parsed_dates)
    best_streak = 1
    run = 1
    for i in range(1, len(asc_dates)):
        if (asc_dates[i] - asc_dates[i - 1]).days == 1:
            run += 1
            if run > best_streak:
                best_streak = run
        else:
            run = 1

    if studied_today:
        alert_level = "ok"
        alert_message = f"Missão cumprida hoje! Sequência ativa de {current_streak} dia(s)."
    elif days_since_last == 1:
        alert_level = "warning"
        alert_message = f"Estude hoje para manter sua sequência de {current_streak} dia(s) viva!"
    else:
        alert_level = "danger"
        alert_message = f"Alerta de constância: {days_since_last} dias sem registrar estudos. Retome o ritmo hoje!"

    return {
        "current_streak": current_streak,
        "best_streak": best_streak,
        "days_since_last": days_since_last,
        "studied_today": studied_today,
        "last_study_date": latest.strftime("%d/%m/%Y"),
        "alert_level": alert_level,
        "alert_message": alert_message
    }


# Helper: Compute Weak Topics Map (A4)
def compute_weak_topics(cursor, user_id: int, limit=12):
    cursor.execute("""
    SELECT t.id as topic_id, t.name as topic_name,
           s.id as subject_id, s.name as subject_name, s.color as subject_color, s.icon as subject_icon,
           COALESCE(SUM(ss.questions_correct), 0) as q_correct,
           COALESCE(SUM(ss.questions_incorrect), 0) as q_incorrect,
           (SELECT COUNT(*) FROM error_notebook e WHERE e.topic_id = t.id AND e.user_id = ? AND e.mastered = 0) as active_errors
    FROM topics t
    JOIN subjects s ON t.subject_id = s.id
    LEFT JOIN study_sessions ss ON ss.topic_id = t.id AND ss.user_id = ?
    WHERE s.user_id = ?
    GROUP BY t.id
    HAVING (q_correct + q_incorrect) > 0 OR active_errors > 0
    """, (user_id, user_id, user_id))
    weak = []
    for r in cursor.fetchall():
        tot = r["q_correct"] + r["q_incorrect"]
        acc = round((r["q_correct"] / tot) * 100, 1) if tot > 0 else 0.0
        is_weak = (tot >= 3 and acc < 60.0) or (tot > 0 and acc < 60.0) or (r["active_errors"] >= 2)
        if is_weak:
            weak.append({
                "topic_id": r["topic_id"],
                "topic_name": r["topic_name"],
                "subject_id": r["subject_id"],
                "subject_name": r["subject_name"],
                "subject_color": r["subject_color"],
                "subject_icon": r["subject_icon"],
                "questions_correct": r["q_correct"],
                "questions_incorrect": r["q_incorrect"],
                "total_questions": tot,
                "accuracy_pct": acc,
                "active_errors": r["active_errors"]
            })
    weak.sort(key=lambda x: (x["accuracy_pct"], -x["active_errors"], -x["total_questions"]))
    return weak[:limit]

# ==================== DASHBOARD API ====================
@app.get("/api/dashboard")
def get_dashboard(request: Request):
    user = require_user(request)
    uid = user["id"]
    with get_db() as conn:
        cursor = conn.cursor()
        
        # User profile
        cursor.execute("SELECT * FROM user_profile WHERE user_id = ? ORDER BY id ASC LIMIT 1", (uid,))
        profile = dict(cursor.fetchone() or {})
        
        # Total study time
        cursor.execute("SELECT COALESCE(SUM(duration_seconds), 0) as total_sec FROM study_sessions WHERE user_id = ?", (uid,))
        total_seconds = cursor.fetchone()["total_sec"]
        total_hours = round(total_seconds / 3600, 1)
        
        # Hours today
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        cursor.execute("SELECT COALESCE(SUM(duration_seconds), 0) as sec_today FROM study_sessions WHERE user_id = ? AND date = ?", (uid, today_str))
        today_seconds = cursor.fetchone()["sec_today"]
        today_minutes = round(today_seconds / 60)
        today_hours = round(today_seconds / 3600, 1)
        today_h = today_seconds // 3600
        today_rem_m = (today_seconds % 3600) // 60
        today_formatted = f"{today_h}h {today_rem_m:02d}m" if today_h > 0 else f"{today_rem_m}m"
        
        # Hours this week (Monday to today)
        today = datetime.date.today()
        start_of_week = (today - datetime.timedelta(days=today.weekday())).strftime("%Y-%m-%d")
        cursor.execute("SELECT COALESCE(SUM(duration_seconds), 0) as sec_week FROM study_sessions WHERE user_id = ? AND date >= ?", (uid, start_of_week))
        week_seconds = cursor.fetchone()["sec_week"]
        week_hours = round(week_seconds / 3600, 1)
        week_h = week_seconds // 3600
        week_rem_m = (week_seconds % 3600) // 60
        week_formatted = f"{week_h}h {week_rem_m:02d}m" if week_h > 0 else f"{week_rem_m}m"

        # Total hours
        total_h = total_seconds // 3600
        total_rem_m = (total_seconds % 3600) // 60
        total_formatted = f"{total_h}h {total_rem_m:02d}m" if total_h > 0 else f"{total_rem_m}m"
        
        # Questions stats
        cursor.execute("""
        SELECT 
            COALESCE(SUM(questions_correct), 0) as total_correct,
            COALESCE(SUM(questions_incorrect), 0) as total_incorrect
        FROM study_sessions
        WHERE user_id = ?
        """, (uid,))
        q_row = cursor.fetchone()
        correct = q_row["total_correct"]
        incorrect = q_row["total_incorrect"]
        total_questions = correct + incorrect
        accuracy_pct = round((correct / total_questions * 100), 1) if total_questions > 0 else 0.0
        
        # Daily goal progress
        daily_goal_minutes = profile.get("daily_goal_minutes", 240)
        daily_progress_pct = min(100.0, round((today_minutes / daily_goal_minutes) * 100, 1)) if daily_goal_minutes > 0 else 0
        
        # Weekly goal progress
        weekly_goal_hours = profile.get("weekly_goal_hours", 25)
        weekly_progress_pct = min(100.0, round((week_hours / weekly_goal_hours) * 100, 1)) if weekly_goal_hours > 0 else 0
        
        # Rank info
        rank_info = get_rank_info(total_seconds)
        
        # Revisions stats
        cursor.execute("SELECT COUNT(*) as count FROM revisions WHERE user_id = ? AND scheduled_date = ? AND completed = 0", (uid, today_str))
        revisions_today = cursor.fetchone()["count"]
        cursor.execute("SELECT COUNT(*) as count FROM revisions WHERE user_id = ? AND scheduled_date < ? AND completed = 0", (uid, today_str))
        revisions_overdue = cursor.fetchone()["count"]
        
        # Last 14 days chart data
        dates_list = []
        hours_list = []
        for i in range(13, -1, -1):
            d = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            d_short = (today - datetime.timedelta(days=i)).strftime("%d/%m")
            dates_list.append(d_short)
            cursor.execute("SELECT COALESCE(SUM(duration_seconds), 0) as sec FROM study_sessions WHERE user_id = ? AND date = ?", (uid, d))
            sec = cursor.fetchone()["sec"]
            hours_list.append(round(sec / 3600, 4))
            
        # Hours by subject
        cursor.execute("""
        SELECT s.name, s.color, COALESCE(SUM(ss.duration_seconds), 0) as total_sec
        FROM subjects s
        LEFT JOIN study_sessions ss ON s.id = ss.subject_id AND ss.user_id = ?
        WHERE s.user_id = ?
        GROUP BY s.id, s.name, s.color
        HAVING total_sec > 0
        ORDER BY total_sec DESC
        LIMIT 7
        """, (uid, uid))
        subject_breakdown = [
            {"name": row["name"], "color": row["color"], "hours": round(row["total_sec"] / 3600, 4), "hours_fmt": format_seconds_hm(row["total_sec"])}
            for row in cursor.fetchall()
        ]
        
        # Recent sessions
        cursor.execute("""
        SELECT ss.id, ss.date, ss.duration_seconds, ss.questions_correct, ss.questions_incorrect, 
               ss.notes, s.name as subject_name, s.color as subject_color, s.icon as subject_icon,
               t.name as topic_name
        FROM study_sessions ss
        JOIN subjects s ON ss.subject_id = s.id
        LEFT JOIN topics t ON ss.topic_id = t.id
        WHERE ss.user_id = ?
        ORDER BY ss.date DESC, ss.id DESC
        LIMIT 6
        """, (uid,))
        recent_sessions = [dict(row) for row in cursor.fetchall()]
        for session in recent_sessions:
            mins = round(session["duration_seconds"] / 60)
            hrs = session["duration_seconds"] // 3600
            rem_mins = (session["duration_seconds"] % 3600) // 60
            session["duration_fmt"] = f"{hrs}h {rem_mins}m" if hrs > 0 else f"{mins}m"

        # Countdown (Dia D)
        cursor.execute("SELECT * FROM exam_countdowns WHERE user_id = ? AND is_active = 1 ORDER BY target_date ASC LIMIT 1", (uid,))
        countdown_row = cursor.fetchone()
        countdown_data = dict(countdown_row) if countdown_row else None
        
        # Law reading today
        cursor.execute("SELECT COALESCE(SUM(articles_read), 0) as arts FROM law_reading_logs WHERE user_id = ? AND date = ?", (uid, today_str))
        law_today = cursor.fetchone()["arts"]
        
        # Total approvals
        cursor.execute("SELECT COUNT(*) as count FROM approvals WHERE user_id = ?", (uid,))
        approvals_count = cursor.fetchone()["count"]
        
        # Latest TAF
        cursor.execute("SELECT * FROM taf_records WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT 1", (uid,))
        taf_row = cursor.fetchone()
        latest_taf = dict(taf_row) if taf_row else None
        if latest_taf:
            is_male = latest_taf.get("is_male", 1) == 1
            pull = latest_taf.get("pull_ups", 0)
            run = latest_taf.get("run_12min_meters", 0)
            sit = latest_taf.get("sit_ups", 0)
            apto = (pull >= (3 if is_male else 1)) and (run >= (2000 if is_male else 1600)) and (sit >= (36 if is_male else 27))
            latest_taf["is_apto"] = apto
            latest_taf["status_label"] = "APTO" if apto else "INAPTO"

        # Tactical Cycle (Próxima Missão Inteligente - Ponderada A1)
        tactical_cycle = compute_tactical_cycle(cursor, uid)

        # Streak & Constância (A3)
        streak_info = compute_streak(cursor, uid)

        # Mapa de Fraquezas por Tópico (A4)
        weak_topics = compute_weak_topics(cursor, uid, limit=6)

        # Active errors count & essays count
        cursor.execute("SELECT COUNT(*) as count FROM error_notebook WHERE user_id = ? AND mastered = 0", (uid,))
        active_errors_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM discursive_essays WHERE user_id = ?", (uid,))
        essays_count = cursor.fetchone()["count"]

        return {
            "profile": profile,
            "rank": rank_info,
            "streak": streak_info,
            "weak_topics": weak_topics,
            "today": {
                "hours": today_hours,
                "minutes": today_minutes,
                "seconds": today_seconds,
                "formatted": today_formatted,
                "goal_minutes": daily_goal_minutes,
                "progress_pct": daily_progress_pct
            },
            "week": {
                "hours": week_hours,
                "seconds": week_seconds,
                "formatted": week_formatted,
                "goal_hours": weekly_goal_hours,
                "progress_pct": weekly_progress_pct
            },
            "total_hours": total_hours,
            "total_formatted": total_formatted,
            "questions": {
                "total": total_questions,
                "correct": correct,
                "incorrect": incorrect,
                "accuracy_pct": accuracy_pct
            },
            "revisions": {
                "today": revisions_today,
                "overdue": revisions_overdue,
                "total_urgent": revisions_today + revisions_overdue
            },
            "charts": {
                "dates": dates_list,
                "daily_hours": hours_list,
                "subject_distribution": subject_breakdown
            },
            "recent_sessions": recent_sessions,
            "countdown": countdown_data,
            "law_today": law_today,
            "approvals_count": approvals_count,
            "latest_taf": latest_taf,
            "tactical_cycle": tactical_cycle,
            "active_errors_count": active_errors_count,
            "essays_count": essays_count
        }

# ==================== SUBJECTS & TOPICS ====================
class SubjectCreate(BaseModel):
    name: str
    category: str = "Jurídica"
    color: str = "#3b82f6"
    icon: str = "fa-shield"
    target_hours: float = 50.0
    weight: float = 1.0

class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    target_hours: Optional[float] = None
    weight: Optional[float] = None

class TopicCreate(BaseModel):
    name: str

@app.get("/api/subjects")
def list_subjects(request: Request):
    user = require_user(request)
    uid = user["id"]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT s.*, 
               COALESCE(s.weight, 1.0) as weight,
               COALESCE(SUM(ss.duration_seconds), 0) as total_seconds,
               COALESCE(SUM(ss.questions_correct), 0) as questions_correct,
               COALESCE(SUM(ss.questions_incorrect), 0) as questions_incorrect
        FROM subjects s
        LEFT JOIN study_sessions ss ON s.id = ss.subject_id AND ss.user_id = ?
        WHERE s.user_id = ?
        GROUP BY s.id
        ORDER BY COALESCE(s.weight, 1.0) DESC, s.category ASC, s.name ASC
        """, (uid, uid))
        subjects = [dict(row) for row in cursor.fetchall()]

        # Precompute per-topic accuracy & active errors in 2 fast queries (A4)
        cursor.execute("""
        SELECT topic_id,
               COALESCE(SUM(questions_correct), 0) as qc,
               COALESCE(SUM(questions_incorrect), 0) as qi
        FROM study_sessions
        WHERE user_id = ? AND topic_id IS NOT NULL
        GROUP BY topic_id
        """, (uid,))
        topic_q_stats = {r["topic_id"]: (r["qc"], r["qi"]) for r in cursor.fetchall()}

        cursor.execute("""
        SELECT topic_id, COUNT(*) as cnt
        FROM error_notebook
        WHERE user_id = ? AND topic_id IS NOT NULL AND mastered = 0
        GROUP BY topic_id
        """, (uid,))
        topic_err_stats = {r["topic_id"]: r["cnt"] for r in cursor.fetchall()}
        
        for subj in subjects:
            subj_id = subj["id"]
            cursor.execute("SELECT * FROM topics WHERE subject_id = ? ORDER BY id ASC", (subj_id,))
            topics = []
            weak_count = 0
            for t_row in cursor.fetchall():
                t = dict(t_row)
                qc, qi = topic_q_stats.get(t["id"], (0, 0))
                tot_tq = qc + qi
                t_acc = round((qc / tot_tq) * 100, 1) if tot_tq > 0 else None
                t_errs = topic_err_stats.get(t["id"], 0)
                is_weak = (tot_tq > 0 and t_acc < 60.0) or (t_errs >= 2)
                if is_weak:
                    weak_count += 1
                t["questions_correct"] = qc
                t["questions_incorrect"] = qi
                t["total_questions"] = tot_tq
                t["accuracy_pct"] = t_acc
                t["active_errors"] = t_errs
                t["is_weak"] = is_weak
                topics.append(t)
            
            # Count completed
            total_topics = len(topics)
            completed_topics = sum(1 for t in topics if t["theory_completed"] and t["summary_completed"] and t["questions_completed"])
            progress_pct = round((completed_topics / total_topics * 100), 1) if total_topics > 0 else 0.0
            
            total_sec = subj["total_seconds"]
            hrs = total_sec // 3600
            mins = (total_sec % 3600) // 60
            subj["hours_fmt"] = f"{hrs}h {mins:02d}m" if hrs > 0 else f"{mins}m"
            subj["hours_num"] = round(total_sec / 3600, 1)
            subj["weight"] = float(subj.get("weight") or 1.0)
            subj["topics"] = topics
            subj["total_topics"] = total_topics
            subj["completed_topics"] = completed_topics
            subj["weak_topics_count"] = weak_count
            subj["progress_pct"] = progress_pct
            
            tot_q = subj["questions_correct"] + subj["questions_incorrect"]
            subj["total_questions"] = tot_q
            subj["accuracy_pct"] = round((subj["questions_correct"] / tot_q * 100), 1) if tot_q > 0 else 0.0

        return subjects

@app.post("/api/subjects")
def create_subject(data: SubjectCreate, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO subjects (user_id, name, category, color, icon, target_hours, weight)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user["id"], data.name, data.category, data.color, data.icon, data.target_hours, max(0.5, min(5.0, data.weight))))
        return {"id": cursor.lastrowid, "message": "Disciplina cadastrada com sucesso!"}

@app.put("/api/subjects/{subject_id}")
def update_subject(subject_id: int, data: SubjectUpdate, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM subjects WHERE id = ? AND user_id = ?", (subject_id, user["id"]))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Disciplina não encontrada")
        new_weight = max(0.5, min(5.0, data.weight)) if data.weight is not None else row["weight"]
        cursor.execute("""
        UPDATE subjects
        SET name = COALESCE(?, name),
            category = COALESCE(?, category),
            color = COALESCE(?, color),
            icon = COALESCE(?, icon),
            target_hours = COALESCE(?, target_hours),
            weight = ?
        WHERE id = ? AND user_id = ?
        """, (data.name, data.category, data.color, data.icon, data.target_hours, new_weight, subject_id, user["id"]))
        return {"message": "Disciplina atualizada com sucesso!"}

@app.delete("/api/subjects/{subject_id}")
def delete_subject(subject_id: int, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM subjects WHERE id = ? AND user_id = ?", (subject_id, user["id"]))
        return {"message": "Disciplina excluída com sucesso!"}

@app.post("/api/subjects/{subject_id}/topics")
def add_topic(subject_id: int, data: TopicCreate, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM subjects WHERE id = ? AND user_id = ?", (subject_id, user["id"]))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Disciplina não encontrada")
        cursor.execute("""
        INSERT INTO topics (subject_id, name)
        VALUES (?, ?)
        """, (subject_id, data.name))
        return {"id": cursor.lastrowid, "message": "Tópico adicionado!"}

@app.put("/api/topics/{topic_id}/toggle")
def toggle_topic(topic_id: int, field: str, request: Request):
    user = require_user(request)
    valid_fields = ["theory_completed", "summary_completed", "questions_completed"]
    if field not in valid_fields:
        raise HTTPException(status_code=400, detail="Campo inválido")
        
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT t.id FROM topics t JOIN subjects s ON t.subject_id = s.id WHERE t.id = ? AND s.user_id = ?", (topic_id, user["id"]))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Tópico não encontrado")
        cursor.execute(f"UPDATE topics SET {field} = CASE WHEN {field} = 1 THEN 0 ELSE 1 END WHERE id = ?", (topic_id,))
        cursor.execute("SELECT * FROM topics WHERE id = ?", (topic_id,))
        updated = dict(cursor.fetchone() or {})
        return {"message": "Tópico atualizado", "topic": updated}

class TopicUpdate(BaseModel):
    name: str
    notes: Optional[str] = ""

@app.get("/api/topics/{topic_id}")
def get_topic(topic_id: int, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT t.* FROM topics t JOIN subjects s ON t.subject_id = s.id WHERE t.id = ? AND s.user_id = ?", (topic_id, user["id"]))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Tópico não encontrado")
        return dict(row)

@app.put("/api/topics/{topic_id}")
def update_topic(topic_id: int, data: TopicUpdate, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE topics SET name = ?, notes = ?
        WHERE id = ? AND subject_id IN (SELECT id FROM subjects WHERE user_id = ?)
        """, (data.name, data.notes or "", topic_id, user["id"]))
        return {"message": "Tópico atualizado com sucesso!"}

@app.delete("/api/topics/{topic_id}")
def delete_topic(topic_id: int, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM topics WHERE id = ? AND subject_id IN (SELECT id FROM subjects WHERE user_id = ?)", (topic_id, user["id"]))
        return {"message": "Tópico excluído"}

# ==================== STUDY SESSIONS ====================
class SessionCreate(BaseModel):
    subject_id: int
    topic_id: Optional[int] = None
    date: Optional[str] = None
    start_time: Optional[str] = None
    duration_seconds: int
    questions_correct: int = 0
    questions_incorrect: int = 0
    notes: Optional[str] = ""
    auto_create_revision: bool = True

@app.get("/api/sessions")
def list_sessions(request: Request, limit: int = 50):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT ss.*, s.name as subject_name, s.color as subject_color, s.icon as subject_icon,
               t.name as topic_name
        FROM study_sessions ss
        JOIN subjects s ON ss.subject_id = s.id
        LEFT JOIN topics t ON ss.topic_id = t.id
        WHERE ss.user_id = ?
        ORDER BY ss.date DESC, ss.id DESC
        LIMIT ?
        """, (user["id"], limit))
        sessions = [dict(row) for row in cursor.fetchall()]
        for s in sessions:
            mins = round(s["duration_seconds"] / 60)
            hrs = s["duration_seconds"] // 3600
            rem_m = (s["duration_seconds"] % 3600) // 60
            s["duration_fmt"] = f"{hrs}h {rem_m}m" if hrs > 0 else f"{mins}m"
        return sessions

@app.post("/api/sessions")
def record_session(data: SessionCreate, request: Request):
    user = require_user(request)
    uid = user["id"]
    session_date = data.date or datetime.date.today().strftime("%Y-%m-%d")
    session_time = data.start_time or datetime.datetime.now().strftime("%H:%M")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO study_sessions (user_id, subject_id, topic_id, date, start_time, duration_seconds, questions_correct, questions_incorrect, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (uid, data.subject_id, data.topic_id, session_date, session_time, data.duration_seconds, data.questions_correct, data.questions_incorrect, data.notes or ""))
        session_id = cursor.lastrowid
        
        if data.auto_create_revision:
            cursor.execute("SELECT name FROM subjects WHERE id = ? AND user_id = ?", (data.subject_id, uid))
            subj_row = cursor.fetchone()
            subj_name = subj_row["name"] if subj_row else "Disciplina"
            
            topic_name = ""
            if data.topic_id:
                cursor.execute("SELECT name FROM topics WHERE id = ?", (data.topic_id,))
                t_row = cursor.fetchone()
                if t_row:
                    topic_name = t_row["name"]
                    
            rev_title = f"Revisão 24h: {topic_name}" if topic_name else f"Revisão 24h: {subj_name}"
            next_day = (datetime.datetime.strptime(session_date, "%Y-%m-%d") + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            
            cursor.execute("""
            INSERT INTO revisions (user_id, subject_id, topic_id, title, scheduled_date, interval_stage, notes)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (uid, data.subject_id, data.topic_id, rev_title, next_day, f"Agendada automaticamente após sessão de {data.duration_seconds // 60} min."))
            
        return {"id": session_id, "message": "Turno de estudo registrado com êxito!"}

@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: int, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM study_sessions WHERE id = ? AND user_id = ?", (session_id, user["id"]))
        return {"message": "Sessão excluída"}

class SessionUpdate(BaseModel):
    subject_id: int
    topic_id: Optional[int] = None
    date: Optional[str] = None
    start_time: Optional[str] = None
    duration_seconds: int
    questions_correct: int = 0
    questions_incorrect: int = 0
    notes: Optional[str] = ""

@app.get("/api/sessions/{session_id}")
def get_session(session_id: int, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT ss.*, s.name as subject_name, t.name as topic_name
        FROM study_sessions ss
        JOIN subjects s ON ss.subject_id = s.id
        LEFT JOIN topics t ON ss.topic_id = t.id
        WHERE ss.id = ? AND ss.user_id = ?
        """, (session_id, user["id"]))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Turno de estudo não encontrado")
        return dict(row)

@app.put("/api/sessions/{session_id}")
def update_session(session_id: int, data: SessionUpdate, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE study_sessions
        SET subject_id = ?, topic_id = ?, date = COALESCE(?, date), start_time = COALESCE(?, start_time),
            duration_seconds = ?, questions_correct = ?, questions_incorrect = ?, notes = ?
        WHERE id = ? AND user_id = ?
        """, (data.subject_id, data.topic_id, data.date, data.start_time, data.duration_seconds, data.questions_correct, data.questions_incorrect, data.notes or "", session_id, user["id"]))
        return {"message": "Turno de estudo atualizado com êxito!"}

# ==================== REVISIONS (SPACED REPETITION) ====================
class RevisionCreate(BaseModel):
    subject_id: int
    topic_id: Optional[int] = None
    title: str
    scheduled_date: str
    interval_stage: int = 1
    notes: Optional[str] = ""

@app.get("/api/revisions")
def list_revisions(request: Request):
    user = require_user(request)
    today = datetime.date.today().strftime("%Y-%m-%d")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT r.*, s.name as subject_name, s.color as subject_color, s.icon as subject_icon,
               t.name as topic_name
        FROM revisions r
        JOIN subjects s ON r.subject_id = s.id
        LEFT JOIN topics t ON r.topic_id = t.id
        WHERE r.user_id = ?
        ORDER BY r.scheduled_date ASC, r.id DESC
        """, (user["id"],))
        all_revisions = [dict(row) for row in cursor.fetchall()]
        
        today_revisions = []
        overdue_revisions = []
        upcoming_revisions = []
        completed_revisions = []
        
        for rev in all_revisions:
            stage = rev["interval_stage"]
            stage_labels = {1: "24 Horas", 2: "7 Dias", 3: "15 Dias", 4: "30 Dias", 5: "Finalizada"}
            rev["stage_label"] = stage_labels.get(stage, f"Etapa {stage}")
            
            if rev["completed"]:
                completed_revisions.append(rev)
            elif rev["scheduled_date"] < today:
                overdue_revisions.append(rev)
            elif rev["scheduled_date"] == today:
                today_revisions.append(rev)
            else:
                upcoming_revisions.append(rev)
                
        return {
            "today": today_revisions,
            "overdue": overdue_revisions,
            "upcoming": upcoming_revisions,
            "completed": completed_revisions,
            "counts": {
                "today": len(today_revisions),
                "overdue": len(overdue_revisions),
                "upcoming": len(upcoming_revisions),
                "completed": len(completed_revisions)
            }
        }

@app.post("/api/revisions")
def create_revision(data: RevisionCreate, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO revisions (user_id, subject_id, topic_id, title, scheduled_date, interval_stage, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user["id"], data.subject_id, data.topic_id, data.title, data.scheduled_date, data.interval_stage, data.notes or ""))
        return {"id": cursor.lastrowid, "message": "Revisão agendada com sucesso!"}

@app.post("/api/revisions/{revision_id}/complete")
def complete_revision(revision_id: int, request: Request):
    user = require_user(request)
    uid = user["id"]
    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM revisions WHERE id = ? AND user_id = ?", (revision_id, uid))
        rev = cursor.fetchone()
        if not rev:
            raise HTTPException(status_code=404, detail="Revisão não encontrada")
            
        current_stage = rev["interval_stage"]
        # Advance spaced repetition stage
        # 1 (24h) -> 2 (7 days)
        # 2 (7d) -> 3 (15 days)
        # 3 (15d) -> 4 (30 days)
        # 4 (30d) -> 5 (Completed)
        next_intervals = {1: 7, 2: 15, 3: 30}
        
        # Mark current as completed
        cursor.execute("""
        UPDATE revisions 
        SET completed = 1, completed_at = ?
        WHERE id = ? AND user_id = ?
        """, (today_str, revision_id, uid))
        
        # Schedule next cycle if not at the final stage
        if current_stage in next_intervals:
            next_days = next_intervals[current_stage]
            next_stage = current_stage + 1
            next_date = (today + datetime.timedelta(days=next_days)).strftime("%Y-%m-%d")
            
            stage_labels = {2: "7 Dias", 3: "15 Dias", 4: "30 Dias"}
            next_title = rev["title"]
            for prefix in ["Revisão 24h:", "Revisão 7 Dias:", "Revisão 15 Dias:", "Revisão 30 Dias:"]:
                if next_title.startswith(prefix):
                    next_title = next_title.replace(prefix, "").strip()
            new_title = f"Revisão {stage_labels[next_stage]}: {next_title}"
            
            cursor.execute("""
            INSERT INTO revisions (user_id, subject_id, topic_id, title, scheduled_date, interval_stage, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (uid, rev["subject_id"], rev["topic_id"], new_title, next_date, next_stage, f"Etapa automática de retenção ({stage_labels[next_stage]})."))
            
            return {
                "message": f"Revisão concluída! Próxima etapa ({stage_labels[next_stage]}) agendada para {next_date}.",
                "next_stage": next_stage,
                "next_date": next_date
            }
        else:
            return {"message": "Protocolo de revisões completamente cumprido para este tópico! Missão cumprida!"}

@app.delete("/api/revisions/{revision_id}")
def delete_revision(revision_id: int, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM revisions WHERE id = ? AND user_id = ?", (revision_id, user["id"]))
        return {"message": "Revisão removida"}

# ==================== NEWS FEED ====================
@app.get("/api/news")
def list_news(category: Optional[str] = None, priority: Optional[str] = None):
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM news_feed WHERE 1=1"
        params = []
        if category and category != "all":
            query += " AND category = ?"
            params.append(category)
        if priority and priority != "all":
            query += " AND priority = ?"
            params.append(priority)
        query += " ORDER BY is_pinned DESC, CASE priority WHEN 'alta' THEN 1 WHEN 'media' THEN 2 ELSE 3 END ASC, id DESC LIMIT 50"
        cursor.execute(query, tuple(params))
        return [dict(row) for row in cursor.fetchall()]

@app.post("/api/news/sync")
def sync_news():
    result = sync_estrategia_news()
    return result

# ==================== RESET DASHBOARD ====================
class ResetDashboardRequest(BaseModel):
    reset_sessions: bool = True
    reset_revisions: bool = False
    reset_topics: bool = False
    reset_simulations: bool = False

@app.post("/api/dashboard/reset")
def reset_dashboard(options: ResetDashboardRequest, request: Request):
    user = require_user(request)
    uid = user["id"]
    with get_db() as conn:
        cursor = conn.cursor()
        cleared = []
        if options.reset_sessions:
            cursor.execute("DELETE FROM study_sessions WHERE user_id = ?", (uid,))
            cleared.append("Horas e turnos de estudos (zerados)")
        if options.reset_revisions:
            cursor.execute("DELETE FROM revisions WHERE user_id = ?", (uid,))
            cleared.append("Revisões agendadas")
        if options.reset_topics:
            cursor.execute("UPDATE topics SET theory_completed = 0, summary_completed = 0, questions_completed = 0 WHERE subject_id IN (SELECT id FROM subjects WHERE user_id = ?)", (uid,))
            cleared.append("Checklist de tópicos do edital")
        if options.reset_simulations:
            cursor.execute("DELETE FROM simulations WHERE user_id = ?", (uid,))
            cleared.append("Histórico de simulados")
            
        return {
            "success": True,
            "message": f"Painel zerado com sucesso! Itens reiniciados: {', '.join(cleared) if cleared else 'Nenhum'}."
        }

# ==================== STUDY PLATFORMS & ARSENAL ====================
class PlatformCreate(BaseModel):
    title: str
    url: str
    category: str = "Banco de Questões"
    icon: Optional[str] = "fa-globe"
    color: Optional[str] = "#3b82f6"
    notes: Optional[str] = ""
    is_pinned: int = 1

@app.get("/api/platforms")
def list_platforms(request: Request, category: Optional[str] = None):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        if category and category != "all":
            cursor.execute("SELECT * FROM study_platforms WHERE user_id = ? AND category = ? ORDER BY is_pinned DESC, id ASC", (user["id"], category))
        else:
            cursor.execute("SELECT * FROM study_platforms WHERE user_id = ? ORDER BY is_pinned DESC, id ASC", (user["id"],))
        return [dict(row) for row in cursor.fetchall()]

@app.post("/api/platforms")
def create_platform(data: PlatformCreate, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        clean_url = data.url.strip()
        if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
            clean_url = "https://" + clean_url
            
        cursor.execute("""
        INSERT INTO study_platforms (user_id, title, url, category, icon, color, notes, is_pinned)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user["id"], data.title, clean_url, data.category, data.icon, data.color, data.notes, data.is_pinned))
        return {"id": cursor.lastrowid, "message": "Plataforma adicionada ao seu Arsenal Tático!"}

@app.delete("/api/platforms/{platform_id}")
def delete_platform(platform_id: int, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM study_platforms WHERE id = ? AND user_id = ?", (platform_id, user["id"]))
        return {"message": "Plataforma removida"}

# ==================== SIMULATIONS & MOCK TESTS (A6 - Por Matéria & Nota de Corte) ====================
class SimCreate(BaseModel):
    title: str
    date: Optional[str] = None
    total_questions: int
    correct_answers: int
    wrong_answers: int
    score: float
    cutoff_score: Optional[float] = 0.0
    target_contest: Optional[str] = ""
    notes: Optional[str] = ""
    subject_breakdown: Optional[List[dict]] = []

def _parse_sim_row(row):
    d = dict(row)
    raw = d.get("subject_breakdown") or "[]"
    try:
        d["subject_breakdown"] = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        d["subject_breakdown"] = []
    d["cutoff_score"] = float(d.get("cutoff_score") or 0.0)
    return d

@app.get("/api/simulations")
def list_simulations(request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM simulations WHERE user_id = ? ORDER BY date DESC, id DESC", (user["id"],))
        return [_parse_sim_row(row) for row in cursor.fetchall()]

@app.get("/api/simulations/analytics")
def simulations_analytics(request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM simulations WHERE user_id = ? ORDER BY date ASC, id ASC", (user["id"],))
        sims = [_parse_sim_row(r) for r in cursor.fetchall()]

        agg = {}
        trend = []
        for s in sims:
            trend.append({
                "id": s["id"],
                "title": s["title"],
                "date": s["date"],
                "score": s["score"],
                "cutoff_score": s["cutoff_score"],
                "total_questions": s["total_questions"],
                "accuracy_pct": round((s["correct_answers"] / s["total_questions"]) * 100, 1) if s["total_questions"] > 0 else 0.0
            })
            for item in s["subject_breakdown"]:
                name = (item.get("subject_name") or "").strip()
                if not name:
                    continue
                if name not in agg:
                    agg[name] = {"subject_name": name, "subject_id": item.get("subject_id"), "correct": 0, "wrong": 0, "total": 0, "sims_count": 0}
                c = int(item.get("correct") or 0)
                w = int(item.get("wrong") or 0)
                t = int(item.get("total") or (c + w))
                agg[name]["correct"] += c
                agg[name]["wrong"] += w
                agg[name]["total"] += t
                agg[name]["sims_count"] += 1

        by_subject = []
        for v in agg.values():
            v["accuracy_pct"] = round((v["correct"] / v["total"]) * 100, 1) if v["total"] > 0 else 0.0
            by_subject.append(v)
        by_subject.sort(key=lambda x: x["accuracy_pct"])

        avg_score = round(sum(s["score"] for s in sims) / len(sims), 1) if sims else 0.0
        latest_cutoff = next((s["cutoff_score"] for s in reversed(sims) if s["cutoff_score"] > 0), 0.0)
        return {
            "total_simulations": len(sims),
            "avg_score": avg_score,
            "latest_cutoff": latest_cutoff,
            "trend": trend,
            "by_subject": by_subject
        }

@app.post("/api/simulations")
def add_simulation(data: SimCreate, request: Request):
    user = require_user(request)
    sim_date = data.date or datetime.date.today().strftime("%Y-%m-%d")
    breakdown_json = json.dumps(data.subject_breakdown or [], ensure_ascii=False)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO simulations (user_id, title, date, total_questions, correct_answers, wrong_answers, score, cutoff_score, target_contest, notes, subject_breakdown)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user["id"], data.title, sim_date, data.total_questions, data.correct_answers, data.wrong_answers, data.score, data.cutoff_score or 0.0, data.target_contest or "", data.notes or "", breakdown_json))
        return {"id": cursor.lastrowid, "message": "Simulado registrado nas Métricas de Combate!"}

@app.delete("/api/simulations/{sim_id}")
def delete_simulation(sim_id: int, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM simulations WHERE id = ? AND user_id = ?", (sim_id, user["id"]))
        return {"message": "Simulado removido"}

class SimUpdate(BaseModel):
    title: str
    date: Optional[str] = None
    total_questions: int
    correct_answers: int
    wrong_answers: int
    score: float
    cutoff_score: Optional[float] = 0.0
    target_contest: Optional[str] = ""
    notes: Optional[str] = ""
    subject_breakdown: Optional[List[dict]] = None

@app.get("/api/simulations/{sim_id}")
def get_simulation(sim_id: int, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM simulations WHERE id = ? AND user_id = ?", (sim_id, user["id"]))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Simulado não encontrado")
        return _parse_sim_row(row)

@app.put("/api/simulations/{sim_id}")
def update_simulation(sim_id: int, data: SimUpdate, request: Request):
    user = require_user(request)
    uid = user["id"]
    with get_db() as conn:
        cursor = conn.cursor()
        if data.subject_breakdown is not None:
            breakdown_json = json.dumps(data.subject_breakdown, ensure_ascii=False)
            cursor.execute("""
            UPDATE simulations
            SET title = ?, date = COALESCE(?, date), total_questions = ?, correct_answers = ?, wrong_answers = ?,
                score = ?, cutoff_score = ?, target_contest = ?, notes = ?, subject_breakdown = ?
            WHERE id = ? AND user_id = ?
            """, (data.title, data.date, data.total_questions, data.correct_answers, data.wrong_answers, data.score, data.cutoff_score or 0.0, data.target_contest or "", data.notes or "", breakdown_json, sim_id, uid))
        else:
            cursor.execute("""
            UPDATE simulations
            SET title = ?, date = COALESCE(?, date), total_questions = ?, correct_answers = ?, wrong_answers = ?,
                score = ?, cutoff_score = ?, target_contest = ?, notes = ?
            WHERE id = ? AND user_id = ?
            """, (data.title, data.date, data.total_questions, data.correct_answers, data.wrong_answers, data.score, data.cutoff_score or 0.0, data.target_contest or "", data.notes or "", sim_id, uid))
        return {"message": "Simulado atualizado com sucesso!"}

# ==================== PROFILE ====================
class ProfileUpdate(BaseModel):
    name: str
    target_role: str
    daily_goal_minutes: int
    weekly_goal_hours: int
    sound_enabled: int = 1

@app.get("/api/profile")
def get_profile(request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profile WHERE user_id = ? ORDER BY id ASC LIMIT 1", (user["id"],))
        return dict(cursor.fetchone() or {})

@app.put("/api/profile")
def update_profile(data: ProfileUpdate, request: Request):
    user = require_user(request)
    uid = user["id"]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE user_profile 
        SET name = ?, target_role = ?, daily_goal_minutes = ?, weekly_goal_hours = ?, sound_enabled = ?
        WHERE user_id = ?
        """, (data.name, data.target_role, data.daily_goal_minutes, data.weekly_goal_hours, data.sound_enabled, uid))
        cursor.execute("UPDATE users SET display_name = ? WHERE id = ?", (data.name, uid))
        return {"message": "Perfil operacional atualizado com sucesso!"}

# ==================== QUADRO DE HONRA (APROVAÇÕES) ====================
class ApprovalCreate(BaseModel):
    contest_name: str
    role: str
    year: int
    position: Optional[str] = ""
    score: Optional[str] = ""
    status: str = "Aprovado"
    badge_icon: Optional[str] = "fa-medal"
    notes: Optional[str] = ""

@app.get("/api/approvals")
def list_approvals(request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM approvals WHERE user_id = ? ORDER BY year DESC, id DESC", (user["id"],))
        return [dict(row) for row in cursor.fetchall()]

@app.post("/api/approvals")
def add_approval(data: ApprovalCreate, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO approvals (user_id, contest_name, role, year, position, score, status, badge_icon, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user["id"], data.contest_name, data.role, data.year, data.position or "", data.score or "", data.status, data.badge_icon or "fa-medal", data.notes or ""))
        return {"id": cursor.lastrowid, "message": "Vitória registrada no Quadro de Honra! Parabéns!"}

@app.delete("/api/approvals/{approval_id}")
def delete_approval(approval_id: int, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM approvals WHERE id = ? AND user_id = ?", (approval_id, user["id"]))
        return {"message": "Registro removido"}

# ==================== MÓDULO TAF OPERACIONAL ====================
class TafCreate(BaseModel):
    date: Optional[str] = None
    pull_ups: int = 0
    pull_up_time: float = 0.0
    run_12min_meters: int = 0
    sit_ups: int = 0
    push_ups: int = 0
    swim_50m_seconds: float = 0.0
    is_male: int = 1
    notes: Optional[str] = ""

@app.get("/api/taf")
def list_taf(request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM taf_records WHERE user_id = ? ORDER BY date DESC, id DESC", (user["id"],))
        records = [dict(row) for row in cursor.fetchall()]
        
        for r in records:
            is_m = r["is_male"] == 1
            pull = r["pull_ups"]
            run = r["run_12min_meters"]
            sit = r["sit_ups"]
            swim = r["swim_50m_seconds"]
            
            # Cebraspe PF/PRF Criteria
            pull_apto = pull >= (3 if is_m else 1)
            run_apto = run >= (2000 if is_m else 1600)
            sit_apto = sit >= (36 if is_m else 27)
            swim_apto = (swim <= 56.0) if swim > 0 else True
            
            is_overall_apto = pull_apto and run_apto and sit_apto and swim_apto
            r["is_apto"] = is_overall_apto
            r["pull_apto"] = pull_apto
            r["run_apto"] = run_apto
            r["sit_apto"] = sit_apto
            r["swim_apto"] = swim_apto
            r["status_label"] = "APTO NO TAF (PADRÃO PF/PRF)" if is_overall_apto else "INAPTO (REFORÇAR TREINO)"
            
        return records

@app.post("/api/taf")
def record_taf(data: TafCreate, request: Request):
    user = require_user(request)
    record_date = data.date or datetime.date.today().strftime("%Y-%m-%d")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO taf_records (user_id, date, pull_ups, pull_up_time, run_12min_meters, sit_ups, push_ups, swim_50m_seconds, is_male, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user["id"], record_date, data.pull_ups, data.pull_up_time, data.run_12min_meters, data.sit_ups, data.push_ups, data.swim_50m_seconds, data.is_male, data.notes or ""))
        return {"id": cursor.lastrowid, "message": "Treino TAF registrado no Boletim de Prontidão Física!"}

@app.delete("/api/taf/{taf_id}")
def delete_taf(taf_id: int, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM taf_records WHERE id = ? AND user_id = ?", (taf_id, user["id"]))
        return {"message": "Treino TAF removido"}

# ==================== COUNTDOWN (DIA D) ====================
class CountdownUpdate(BaseModel):
    title: str
    target_date: str
    target_time: Optional[str] = "08:00"

@app.get("/api/countdown")
def get_countdown(request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM exam_countdowns WHERE user_id = ? AND is_active = 1 ORDER BY target_date ASC LIMIT 1", (user["id"],))
        row = cursor.fetchone()
        return dict(row) if row else None

@app.post("/api/countdown")
def update_countdown(data: CountdownUpdate, request: Request):
    user = require_user(request)
    uid = user["id"]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM exam_countdowns WHERE user_id = ? AND is_active = 1 ORDER BY id DESC LIMIT 1", (uid,))
        active = cursor.fetchone()
        if active:
            cursor.execute("""
            UPDATE exam_countdowns
            SET title = ?, target_date = ?, target_time = ?, is_active = 1
            WHERE id = ? AND user_id = ?
            """, (data.title, data.target_date, data.target_time or "08:00", active["id"], uid))
            cursor.execute("UPDATE exam_countdowns SET is_active = 0 WHERE user_id = ? AND id != ?", (uid, active["id"]))
        else:
            cursor.execute("UPDATE exam_countdowns SET is_active = 0 WHERE user_id = ?", (uid,))
            cursor.execute("""
            INSERT INTO exam_countdowns (user_id, title, target_date, target_time, is_active)
            VALUES (?, ?, ?, ?, 1)
            """, (uid, data.title, data.target_date, data.target_time or "08:00"))
        return {"message": "Contagem regressiva do Dia D atualizada com sucesso!"}

# ==================== RADAR DE LEI SECA ====================
class LawReadingCreate(BaseModel):
    date: Optional[str] = None
    code_name: str
    articles_read: int
    notes: Optional[str] = ""

@app.get("/api/law-readings")
def list_law_readings(request: Request):
    user = require_user(request)
    uid = user["id"]
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM law_reading_logs WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT 50", (uid,))
        logs = [dict(row) for row in cursor.fetchall()]
        
        # Today total
        cursor.execute("SELECT COALESCE(SUM(articles_read), 0) as tot FROM law_reading_logs WHERE user_id = ? AND date = ?", (uid, today_str))
        today_total = cursor.fetchone()["tot"]
        
        # All time total
        cursor.execute("SELECT COALESCE(SUM(articles_read), 0) as tot FROM law_reading_logs WHERE user_id = ?", (uid,))
        all_time_total = cursor.fetchone()["tot"]
        
        # Breakdown by code
        cursor.execute("""
        SELECT code_name, SUM(articles_read) as total_articles
        FROM law_reading_logs
        WHERE user_id = ?
        GROUP BY code_name
        ORDER BY total_articles DESC
        """, (uid,))
        breakdown = [dict(row) for row in cursor.fetchall()]
        
        return {
            "logs": logs,
            "today_total": today_total,
            "all_time_total": all_time_total,
            "breakdown": breakdown
        }

@app.post("/api/law-readings")
def log_law_reading(data: LawReadingCreate, request: Request):
    user = require_user(request)
    log_date = data.date or datetime.date.today().strftime("%Y-%m-%d")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO law_reading_logs (user_id, date, code_name, articles_read, notes)
        VALUES (?, ?, ?, ?, ?)
        """, (user["id"], log_date, data.code_name, data.articles_read, data.notes or ""))
        return {"id": cursor.lastrowid, "message": f"{data.articles_read} artigos registrados no Radar de Lei Seca!"}

@app.delete("/api/law-readings/{log_id}")
def delete_law_reading(log_id: int, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM law_reading_logs WHERE id = ? AND user_id = ?", (log_id, user["id"]))
        return {"message": "Registro de lei seca excluído"}

# ==================== CADERNO DE ERROS (DOSSIÊ DE VULNERABILIDADES) ====================
class ErrorCreate(BaseModel):
    subject_id: int
    topic_id: Optional[int] = None
    banca: Optional[str] = "Cebraspe"
    question_ref: Optional[str] = ""
    error_reason: str
    question_statement: Optional[str] = ""
    bizu_notes: str

@app.get("/api/errors")
def list_errors(request: Request, banca: Optional[str] = None, reason: Optional[str] = None, mastered: Optional[int] = None):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
        SELECT e.*, s.name as subject_name, s.color as subject_color, s.icon as subject_icon,
               t.name as topic_name
        FROM error_notebook e
        JOIN subjects s ON e.subject_id = s.id
        LEFT JOIN topics t ON e.topic_id = t.id
        WHERE e.user_id = ?
        """
        params = [user["id"]]
        if banca and banca != "all":
            query += " AND e.banca = ?"
            params.append(banca)
        if reason and reason != "all":
            query += " AND e.error_reason = ?"
            params.append(reason)
        if mastered is not None:
            query += " AND e.mastered = ?"
            params.append(mastered)
            
        query += " ORDER BY e.mastered ASC, e.id DESC"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

@app.post("/api/errors")
def add_error(data: ErrorCreate, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO error_notebook (user_id, subject_id, topic_id, banca, question_ref, error_reason, question_statement, bizu_notes, mastered)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (user["id"], data.subject_id, data.topic_id, data.banca or "Cebraspe", data.question_ref or "", data.error_reason, data.question_statement or "", data.bizu_notes))
        return {"id": cursor.lastrowid, "message": "Erro catalogado no Dossiê de Vulnerabilidades!"}

@app.put("/api/errors/{error_id}/toggle-mastered")
def toggle_error_mastered(error_id: int, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE error_notebook SET mastered = CASE WHEN mastered = 1 THEN 0 ELSE 1 END WHERE id = ? AND user_id = ?", (error_id, user["id"]))
        cursor.execute("SELECT mastered FROM error_notebook WHERE id = ? AND user_id = ?", (error_id, user["id"]))
        row = cursor.fetchone()
        is_m = row["mastered"] == 1 if row else False
        msg = "Vulnerabilidade superada e dominada com louvor!" if is_m else "Vulnerabilidade reaberta para revisão!"
        return {"mastered": is_m, "message": msg}

@app.delete("/api/errors/{error_id}")
def delete_error(error_id: int, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM error_notebook WHERE id = ? AND user_id = ?", (error_id, user["id"]))
        return {"message": "Erro removido do caderno"}

class ErrorUpdate(BaseModel):
    subject_id: int
    topic_id: Optional[int] = None
    banca: Optional[str] = "Cebraspe"
    question_ref: Optional[str] = ""
    error_reason: str
    question_statement: Optional[str] = ""
    bizu_notes: str

@app.get("/api/errors/{error_id}")
def get_error(error_id: int, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT e.*, s.name as subject_name, t.name as topic_name
        FROM error_notebook e
        JOIN subjects s ON e.subject_id = s.id
        LEFT JOIN topics t ON e.topic_id = t.id
        WHERE e.id = ? AND e.user_id = ?
        """, (error_id, user["id"]))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Erro não encontrado")
        return dict(row)

@app.put("/api/errors/{error_id}")
def update_error(error_id: int, data: ErrorUpdate, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE error_notebook
        SET subject_id = ?, topic_id = ?, banca = ?, question_ref = ?, error_reason = ?, question_statement = ?, bizu_notes = ?
        WHERE id = ? AND user_id = ?
        """, (data.subject_id, data.topic_id, data.banca or "Cebraspe", data.question_ref or "", data.error_reason, data.question_statement or "", data.bizu_notes, error_id, user["id"]))
        return {"message": "Vulnerabilidade atualizada no Caderno de Erros!"}

# ==================== OFICINA DE DISCURSIVAS & REDAÇÕES ====================
class EssayCreate(BaseModel):
    title: str
    date: Optional[str] = None
    agency: Optional[str] = "Polícia Federal"
    lines_count: Optional[int] = 30
    score: float = 0.0
    max_score: float = 10.0
    notes: Optional[str] = ""

@app.get("/api/essays")
def list_essays(request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM discursive_essays WHERE user_id = ? ORDER BY date DESC, id DESC", (user["id"],))
        return [dict(row) for row in cursor.fetchall()]

@app.post("/api/essays")
def add_essay(data: EssayCreate, request: Request):
    user = require_user(request)
    essay_date = data.date or datetime.date.today().strftime("%Y-%m-%d")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO discursive_essays (user_id, title, date, agency, lines_count, score, max_score, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user["id"], data.title, essay_date, data.agency or "Polícia Federal", data.lines_count or 30, data.score, data.max_score, data.notes or ""))
        return {"id": cursor.lastrowid, "message": "Redação registrada na Oficina de Discursivas!"}

@app.delete("/api/essays/{essay_id}")
def delete_essay(essay_id: int, request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM discursive_essays WHERE id = ? AND user_id = ?", (essay_id, user["id"]))
        return {"message": "Redação removida"}

@app.get("/api/essay-prompts")
def list_essay_prompts():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM essay_prompts ORDER BY id ASC")
        return [dict(row) for row in cursor.fetchall()]

# ==================== CICLO TÁTICO (PRÓXIMA MISSÃO) ====================
@app.get("/api/cycle/next")
def get_next_cycle_mission(request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        return compute_tactical_cycle(cursor, user["id"])


# ==================== PLANO DO DIA AUTOMÁTICO (A2) ====================
@app.get("/api/daily-plan")
def generate_daily_plan(request: Request, minutes: int = 120):
    user = require_user(request)
    uid = user["id"]
    avail = max(30, min(720, int(minutes)))
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    with get_db() as conn:
        cursor = conn.cursor()
        ranked_subjects = compute_tactical_cycle(cursor, uid, return_all=True)

        # Pending urgent revisions
        cursor.execute("""
        SELECT r.id, r.title, r.subject_id, r.topic_id, s.name as subject_name, s.color as subject_color
        FROM revisions r
        JOIN subjects s ON r.subject_id = s.id
        WHERE r.user_id = ? AND r.completed = 0 AND r.scheduled_date <= ?
        ORDER BY r.scheduled_date ASC LIMIT 3
        """, (uid, today_str))
        urgent_revs = [dict(r) for r in cursor.fetchall()]

        weak_topics = compute_weak_topics(cursor, uid, limit=3)

        blocks = []
        remaining = avail

        # 1. Bloco de Revisão / Fraquezas (se houver)
        if urgent_revs and remaining >= 45:
            rev_mins = min(25, max(15, round(avail * 0.15 / 5) * 5))
            first_rev = urgent_revs[0]
            blocks.append({
                "type": "revision",
                "badge": "REVISÃO URGENTE",
                "title": first_rev["title"],
                "subtitle": f"{len(urgent_revs)} revisão(ões) pendente(s) hoje/atrasadas • {first_rev['subject_name']}",
                "minutes": rev_mins,
                "subject_id": first_rev["subject_id"],
                "topic_id": first_rev["topic_id"],
                "color": "#f43f5e",
                "icon": "fa-rotate"
            })
            remaining -= rev_mins
        elif weak_topics and remaining >= 60:
            wk_mins = min(25, max(15, round(avail * 0.15 / 5) * 5))
            wt = weak_topics[0]
            blocks.append({
                "type": "weakness",
                "badge": "BLINDAR FRAQUEZA",
                "title": f"{wt['subject_name']} — {wt['topic_name']}",
                "subtitle": f"Acerto atual: {wt['accuracy_pct']}% ({wt['questions_correct']}A/{wt['questions_incorrect']}E) • Revisar bizus + questões",
                "minutes": wk_mins,
                "subject_id": wt["subject_id"],
                "topic_id": wt["topic_id"],
                "color": "#ef4444",
                "icon": "fa-triangle-exclamation"
            })
            remaining -= wk_mins

        # 2. Bloco de Lei Seca (15-20 min se tempo total >= 60 min)
        law_block = None
        if avail >= 60 and remaining >= 45:
            law_mins = 15 if avail < 150 else 20
            # Sugerir lei menos lida recentemente
            cursor.execute("""
            SELECT code_name, COALESCE(SUM(articles_read), 0) as total
            FROM law_reading_logs
            WHERE user_id = ?
            GROUP BY code_name
            """, (uid,))
            law_counts = {r["code_name"]: r["total"] for r in cursor.fetchall()}
            priority_laws = [
                "Estatuto da PC-TO (Lei 1.654/06)",
                "Código de Processo Penal (CPP)",
                "Código Penal (CP)",
                "Constituição Federal (CF/88)",
                "Lei de Drogas (11.343/06)"
            ]
            priority_laws.sort(key=lambda name: law_counts.get(name, 0))
            law_target = priority_laws[0]
            law_block = {
                "type": "law",
                "badge": "LEI SECA DIÁRIA",
                "title": f"Leitura de Lei Seca: {law_target}",
                "subtitle": "Meta: 15 a 20 artigos grifando prazos, exceções e pegadinhas",
                "minutes": law_mins,
                "subject_id": None,
                "topic_id": None,
                "color": "#a855f7",
                "icon": "fa-scale-balanced"
            }
            remaining -= law_mins

        # 3. Blocos de Estudo Principal + Secundário (ponderados pelo peso do edital)
        def pick_next_topic(subj_id):
            cursor.execute("""
            SELECT id, name FROM topics
            WHERE subject_id = ? AND (theory_completed = 0 OR summary_completed = 0 OR questions_completed = 0)
            ORDER BY id ASC LIMIT 1
            """, (subj_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

        if ranked_subjects:
            if remaining <= 55 or len(ranked_subjects) == 1:
                s1 = ranked_subjects[0]
                t1 = pick_next_topic(s1["id"])
                blocks.append({
                    "type": "study",
                    "badge": f"MISSÃO #1 • PESO {s1['weight']:.1f}x",
                    "title": s1["name"],
                    "subtitle": f"Tópico: {t1['name']}" if t1 else "Revisão geral e bateria de questões",
                    "minutes": remaining,
                    "subject_id": s1["id"],
                    "topic_id": t1["id"] if t1 else None,
                    "color": s1["color"],
                    "icon": s1["icon"]
                })
            else:
                # Divide remaining into 2 or 3 blocks depending on total time
                num_slots = 3 if remaining >= 150 and len(ranked_subjects) >= 3 else 2
                if num_slots == 2:
                    m1 = max(25, round((remaining * 0.55) / 5) * 5)
                    m2 = remaining - m1
                    slots = [(ranked_subjects[0], m1, "TEORIA + QUESTÕES"), (ranked_subjects[1], m2, "BATERIA DE QUESTÕES")]
                else:
                    m1 = max(40, round((remaining * 0.40) / 5) * 5)
                    m2 = max(35, round((remaining * 0.35) / 5) * 5)
                    m3 = remaining - m1 - m2
                    slots = [
                        (ranked_subjects[0], m1, "TEORIA + RESUMO"),
                        (ranked_subjects[1], m2, "BATERIA DE QUESTÕES"),
                        (ranked_subjects[2], m3, "FIXAÇÃO RÁPIDA")
                    ]
                for idx_s, (subj, mins, mode_label) in enumerate(slots):
                    t = pick_next_topic(subj["id"])
                    blocks.append({
                        "type": "questions" if "QUESTÕES" in mode_label else "study",
                        "badge": f"MISSÃO #{idx_s + 1} • PESO {subj['weight']:.1f}x • {mode_label}",
                        "title": subj["name"],
                        "subtitle": f"Tópico: {t['name']}" if t else "Revisão estratégica + questões da banca",
                        "minutes": mins,
                        "subject_id": subj["id"],
                        "topic_id": t["id"] if t else None,
                        "color": subj["color"],
                        "icon": subj["icon"]
                    })

        if law_block:
            blocks.append(law_block)

        total_planned = sum(b["minutes"] for b in blocks)
        return {
            "total_minutes": total_planned,
            "blocks": blocks
        }


# ==================== MAPA DE FRAQUEZAS POR TÓPICO (A4) ====================
@app.get("/api/weak-topics")
def list_weak_topics(request: Request, limit: int = 20):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        return compute_weak_topics(cursor, user["id"], limit=limit)

@app.post("/api/weak-topics/{topic_id}/schedule-revision")
def schedule_weak_topic_revision(topic_id: int, request: Request):
    user = require_user(request)
    uid = user["id"]
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT t.id, t.name as topic_name, t.subject_id, s.name as subject_name
        FROM topics t
        JOIN subjects s ON t.subject_id = s.id
        WHERE t.id = ? AND s.user_id = ?
        """, (topic_id, uid))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Tópico não encontrado")

        title = f"Reforço Crítico: {row['topic_name']}"
        cursor.execute("""
        SELECT id FROM revisions
        WHERE user_id = ? AND topic_id = ? AND completed = 0 AND scheduled_date <= ?
        """, (uid, topic_id, today_str))
        if cursor.fetchone():
            return {"message": "Já existe uma revisão pendente para este tópico!"}

        cursor.execute("""
        INSERT INTO revisions (user_id, subject_id, topic_id, title, scheduled_date, interval_stage, notes)
        VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (uid, row["subject_id"], topic_id, title, today_str, f"Enviado do Mapa de Fraquezas ({row['subject_name']}) para correção imediata."))
        return {"id": cursor.lastrowid, "message": f"Tópico '{row['topic_name']}' enviado para Revisão Urgente de hoje!"}


# ==================== IMPORTADOR DE EDITAL VERTICALIZADO (A5) ====================
def _norm_key(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text or "")
    cleaned = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    cleaned = re.sub(r"[^a-z0-9]+", " ", cleaned.lower()).strip()
    return cleaned

def parse_edital_text(raw_text: str):
    """
    Extrai matérias e tópicos de texto colado de editais brasileiros.
    Suporta formatos:
      - 'DIREITO PENAL:' ou 'MATÉRIA: Direito Penal (Peso 3)' ou '1. DIREITO PENAL'
      - Tópicos em linhas abaixo ('1.1 ...', '- ...', '• ...') OU separados por ';'
    """
    palette = ["#ef4444", "#f97316", "#3b82f6", "#06b6d4", "#8b5cf6", "#10b981", "#eab308", "#6366f1", "#ec4899", "#f59e0b", "#14b8a6"]
    lines = [l.strip() for l in (raw_text or "").replace("\r\n", "\n").split("\n") if l.strip()]
    subjects = []
    current = None

    def start_subject(raw_name: str, weight: float = 1.5):
        nonlocal current
        name = re.sub(r"^(?:mat[eé]ria|disciplina)\s*:\s*", "", raw_name, flags=re.I)
        name = re.sub(r"^\d+[\.\)\-\s]+", "", name)
        name = name.strip(" :*#-•")
        if not name:
            return
        # Title-case ALL CAPS headings cleanly while preserving acronyms
        if name.isupper() and len(name) > 4:
            words = name.split()
            small = {"de", "da", "do", "das", "dos", "e", "em", "na", "no", "para", "com", "a", "o"}
            acronyms = {"pc-to", "pc", "to", "pf", "prf", "pm", "cf", "cp", "cpp", "ctb", "ti", "rlm", "dh", "sus", "lgpd"}
            formatted = []
            for i, w in enumerate(words):
                wl = w.lower()
                if wl in acronyms:
                    formatted.append(w.upper())
                elif i > 0 and wl in small:
                    formatted.append(wl)
                else:
                    formatted.append(wl.capitalize())
            name = " ".join(formatted)
        idx = len(subjects) % len(palette)
        current = {
            "name": name,
            "weight": max(0.5, min(5.0, weight)),
            "color": palette[idx],
            "topics": []
        }
        subjects.append(current)

    def add_topics_from_chunk(chunk: str):
        if current is None:
            return
        # Split by semicolon or numbered items inline (e.g. "1. Foo. 2. Bar")
        parts = [p.strip() for p in re.split(r"\s*;\s*", chunk) if p.strip()]
        for p in parts:
            t = re.sub(r"^(?:[-•*–—]+|\d+(?:\.\d+)*[\.\)\-]?\s+)", "", p).strip(" .;:-")
            if len(t) >= 3 and t not in current["topics"]:
                current["topics"].append(t[:180])

    for line in lines:
        # Extract optional explicit weight like "(Peso 3)" or "[Peso 2.5]"
        weight = 1.5
        wm = re.search(r"[\(\[]\s*peso\s*[:=]?\s*(\d+(?:[\.,]\d+)?)\s*[\)\]]", line, flags=re.I)
        if wm:
            weight = float(wm.group(1).replace(",", "."))
            line = (line[:wm.start()] + line[wm.end():]).strip()

        is_explicit_hdr = bool(re.match(r"^(?:mat[eé]ria|disciplina|#+)\s*:?", line, flags=re.I))
        is_bullet = bool(re.match(r"^[-•*–—]\s+", line))
        is_subnum = bool(re.match(r"^\d+\.\d+", line))

        # Inline "DIREITO PENAL: 1. Tópico A; 2. Tópico B"
        if ":" in line and not is_bullet and not is_subnum:
            left, right = line.split(":", 1)
            left_clean = left.strip(" *#-•")
            if is_explicit_hdr and not right.strip():
                start_subject(left_clean, weight)
                continue
            elif is_explicit_hdr:
                # "MATÉRIA: Direito Penal"
                start_subject(right.strip(), weight)
                continue
            elif 3 <= len(left_clean) <= 65 and (left_clean.isupper() or re.match(r"^\d+[\.\)]\s*[A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ]", left_clean)):
                start_subject(left_clean, weight)
                if right.strip():
                    add_topics_from_chunk(right.strip())
                continue

        # Standalone heading line (ALL CAPS, markdown heading, or short title ending with :)
        letters_only = re.sub(r"[^A-Za-zÀ-ÿ]", "", line)
        if not is_bullet and not is_subnum and (
            line.endswith(":")
            or line.startswith("#")
            or (len(letters_only) >= 4 and letters_only.isupper() and len(line) <= 75 and ";" not in line)
        ):
            start_subject(line, weight)
            continue

        # Otherwise treat as topic(s)
        if current is None:
            start_subject("Conhecimentos Gerais", 1.5)
        add_topics_from_chunk(line)

    # Filter out empty subjects without topics only if there are other valid ones
    return [s for s in subjects if s["name"]]

class EditalImportRequest(BaseModel):
    text: str
    mode: str = "merge"  # merge (mantém tudo e soma novos) | replace_unused (remove matérias sem horas que não estão no novo edital)

@app.post("/api/edital/preview")
def preview_edital_import(payload: EditalImportRequest, request: Request):
    user = require_user(request)
    parsed = parse_edital_text(payload.text)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM subjects WHERE user_id = ?", (user["id"],))
        existing = {_norm_key(r["name"]): dict(r) for r in cursor.fetchall()}

    for s in parsed:
        match = existing.get(_norm_key(s["name"]))
        s["matched_existing"] = match["name"] if match else None
    return {
        "subjects_count": len(parsed),
        "topics_count": sum(len(s["topics"]) for s in parsed),
        "subjects": parsed
    }

@app.post("/api/edital/import")
def import_edital(payload: EditalImportRequest, request: Request):
    user = require_user(request)
    uid = user["id"]
    parsed = parse_edital_text(payload.text)
    if not parsed:
        raise HTTPException(status_code=400, detail="Não foi possível identificar matérias no texto colado. Coloque cada matéria em MAIÚSCULAS ou com 'MATÉRIA: Nome'.")

    subjects_added = 0
    subjects_matched = 0
    topics_added = 0
    kept_subject_ids = set()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM subjects WHERE user_id = ?", (uid,))
        existing_map = {_norm_key(r["name"]): r["id"] for r in cursor.fetchall()}

        for s in parsed:
            norm = _norm_key(s["name"])
            if norm in existing_map:
                subj_id = existing_map[norm]
                subjects_matched += 1
                cursor.execute("UPDATE subjects SET weight = ? WHERE id = ? AND user_id = ?", (s["weight"], subj_id, uid))
            else:
                cursor.execute("""
                INSERT INTO subjects (user_id, name, category, color, icon, target_hours, weight)
                VALUES (?, ?, 'Específica', ?, 'fa-book-open', 40.0, ?)
                """, (uid, s["name"], s["color"], s["weight"]))
                subj_id = cursor.lastrowid
                existing_map[norm] = subj_id
                subjects_added += 1

            kept_subject_ids.add(subj_id)

            cursor.execute("SELECT name FROM topics WHERE subject_id = ?", (subj_id,))
            existing_topics = {_norm_key(r["name"]) for r in cursor.fetchall()}
            for t in s["topics"]:
                if _norm_key(t) not in existing_topics:
                    cursor.execute("INSERT INTO topics (subject_id, name) VALUES (?, ?)", (subj_id, t))
                    existing_topics.add(_norm_key(t))
                    topics_added += 1

        removed_unused = 0
        if payload.mode == "replace_unused" and kept_subject_ids:
            cursor.execute("""
            SELECT s.id FROM subjects s
            LEFT JOIN study_sessions ss ON ss.subject_id = s.id AND ss.user_id = ?
            WHERE s.user_id = ?
            GROUP BY s.id
            HAVING COALESCE(SUM(ss.duration_seconds), 0) = 0
            """, (uid, uid))
            for r in cursor.fetchall():
                if r["id"] not in kept_subject_ids:
                    cursor.execute("DELETE FROM subjects WHERE id = ? AND user_id = ?", (r["id"], uid))
                    removed_unused += 1

    return {
        "success": True,
        "subjects_added": subjects_added,
        "subjects_matched": subjects_matched,
        "topics_added": topics_added,
        "removed_unused": removed_unused,
        "message": f"Edital importado! {subjects_added} nova(s) matéria(s), {subjects_matched} já existente(s) preservada(s) e {topics_added} tópico(s) adicionado(s)."
    }

# ==================== BACKUP & RESTAURAÇÃO TOTAL ====================
@app.get("/api/backup/export")
def export_backup(request: Request):
    user = require_user(request)
    uid = user["id"]
    with get_db() as conn:
        cursor = conn.cursor()
        user_tables = [
            "user_profile", "subjects", "study_sessions",
            "revisions", "simulations", "study_platforms",
            "approvals", "taf_records", "exam_countdowns",
            "law_reading_logs", "error_notebook", "discursive_essays"
        ]
        backup_data = {
            "version": "3.0-alem-da-meta",
            "username": user["username"],
            "exported_at": datetime.datetime.now().isoformat(),
            "tables": {}
        }
        for table in user_tables:
            cursor.execute(f"SELECT * FROM {table} WHERE user_id = ?", (uid,))
            backup_data["tables"][table] = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT t.* FROM topics t JOIN subjects s ON t.subject_id = s.id WHERE s.user_id = ?", (uid,))
        backup_data["tables"]["topics"] = [dict(row) for row in cursor.fetchall()]
        return backup_data

class BackupImport(BaseModel):
    data: dict

@app.post("/api/backup/import")
def import_backup(payload: BackupImport, request: Request):
    user = require_user(request)
    uid = user["id"]
    data = payload.data
    tables = data.get("tables", {})
    if not tables:
        raise HTTPException(status_code=400, detail="Formato de backup inválido ou vazio.")

    with get_db() as conn:
        cursor = conn.cursor()
        # Import subjects + topics mapping old subject_id -> new subject_id cleanly
        subj_id_map = {}
        topic_id_map = {}

        if tables.get("user_profile"):
            p0 = tables["user_profile"][0]
            cursor.execute("""
            UPDATE user_profile SET name = ?, target_role = ?, daily_goal_minutes = ?, weekly_goal_hours = ?, sound_enabled = ?
            WHERE user_id = ?
            """, (p0.get("name", user["display_name"]), p0.get("target_role", "Concurso Público"), p0.get("daily_goal_minutes", 240), p0.get("weekly_goal_hours", 25), p0.get("sound_enabled", 1), uid))

        if tables.get("subjects"):
            cursor.execute("DELETE FROM subjects WHERE user_id = ?", (uid,))
            for s in tables["subjects"]:
                cursor.execute("""
                INSERT INTO subjects (user_id, name, category, color, icon, target_hours, weight)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (uid, s["name"], s.get("category", "Jurídica"), s.get("color", "#3b82f6"), s.get("icon", "fa-book"), s.get("target_hours", 50.0), s.get("weight", 1.0)))
                subj_id_map[s["id"]] = cursor.lastrowid

            for t in tables.get("topics", []):
                new_sid = subj_id_map.get(t["subject_id"])
                if new_sid:
                    cursor.execute("""
                    INSERT INTO topics (subject_id, name, theory_completed, summary_completed, questions_completed, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (new_sid, t["name"], t.get("theory_completed", 0), t.get("summary_completed", 0), t.get("questions_completed", 0), t.get("notes", "")))
                    topic_id_map[t["id"]] = cursor.lastrowid

        for simple_tbl, cols in [
            ("study_sessions", ["date", "start_time", "duration_seconds", "questions_correct", "questions_incorrect", "notes"]),
            ("revisions", ["title", "scheduled_date", "interval_stage", "completed", "completed_at", "notes"]),
            ("error_notebook", ["banca", "question_ref", "error_reason", "question_statement", "bizu_notes", "mastered"]),
        ]:
            if simple_tbl in tables:
                cursor.execute(f"DELETE FROM {simple_tbl} WHERE user_id = ?", (uid,))
                for r in tables[simple_tbl]:
                    new_sid = subj_id_map.get(r.get("subject_id"))
                    if not new_sid:
                        continue
                    new_tid = topic_id_map.get(r.get("topic_id")) if r.get("topic_id") else None
                    ph = ", ".join(["?"] * (len(cols) + 3))
                    cn = ", ".join(["user_id", "subject_id", "topic_id"] + cols)
                    vals = [uid, new_sid, new_tid] + [r.get(c) for c in cols]
                    cursor.execute(f"INSERT INTO {simple_tbl} ({cn}) VALUES ({ph})", vals)

        for flat_tbl, cols in [
            ("simulations", ["title", "date", "total_questions", "correct_answers", "wrong_answers", "score", "cutoff_score", "target_contest", "notes", "subject_breakdown"]),
            ("study_platforms", ["title", "url", "category", "icon", "color", "notes", "is_pinned"]),
            ("approvals", ["contest_name", "role", "year", "position", "score", "status", "badge_icon", "notes"]),
            ("taf_records", ["date", "pull_ups", "pull_up_time", "run_12min_meters", "sit_ups", "push_ups", "swim_50m_seconds", "is_male", "notes"]),
            ("exam_countdowns", ["title", "target_date", "target_time", "is_active"]),
            ("law_reading_logs", ["date", "code_name", "articles_read", "notes"]),
            ("discursive_essays", ["title", "date", "agency", "lines_count", "score", "max_score", "notes"]),
        ]:
            if flat_tbl in tables:
                cursor.execute(f"DELETE FROM {flat_tbl} WHERE user_id = ?", (uid,))
                for r in tables[flat_tbl]:
                    ph = ", ".join(["?"] * (len(cols) + 1))
                    cn = ", ".join(["user_id"] + cols)
                    vals = [uid] + [r.get(c) for c in cols]
                    cursor.execute(f"INSERT INTO {flat_tbl} ({cn}) VALUES ({ph})", vals)

        return {"success": True, "message": "Backup da sua conta restaurado com sucesso!"}

# ==================== NETWORK & LAN ACCESS INFO ====================
def get_system_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = '127.0.0.1'
    finally:
        s.close()
    return ip

@app.get("/api/network-info")
def get_network_info(request: Request):
    ip = get_system_lan_ip()
    port = request.url.port or 8000
    return {
        "local_ip": ip,
        "port": port,
        "lan_url": f"http://{ip}:{port}",
        "local_url": f"http://localhost:{port}"
    }

# ==================== GLOBAL SEARCH (COMMAND PALETTE) ====================
@app.get("/api/search")
def global_search(q: str, request: Request):
    user = require_user(request)
    uid = user["id"]
    term = q.strip()
    if not term or len(term) < 2:
        return {"query": term, "total": 0, "results": []}

    like_pat = f"%{term}%"
    results = []

    with get_db() as conn:
        cursor = conn.cursor()

        # 1. Subjects & Topics
        cursor.execute("""
        SELECT s.id as subject_id, s.name as subject_name, s.color as subject_color, s.icon as subject_icon,
               t.id as topic_id, t.name as topic_name, COALESCE(t.notes, '') as topic_notes
        FROM topics t
        JOIN subjects s ON t.subject_id = s.id
        WHERE s.user_id = ? AND (t.name LIKE ? OR t.notes LIKE ? OR s.name LIKE ?)
        LIMIT 10
        """, (uid, like_pat, like_pat, like_pat))
        for r in cursor.fetchall():
            results.append({
                "type": "topic",
                "category": "Dossiê de Matérias",
                "icon": r["subject_icon"] or "fa-book",
                "color": r["subject_color"] or "#3b82f6",
                "title": r["topic_name"],
                "subtitle": f"Disciplina: {r['subject_name']}",
                "detail": r["topic_notes"],
                "tab": "subjects",
                "ref_id": r["subject_id"]
            })

        # 2. Error Notebook
        cursor.execute("""
        SELECT e.id, e.banca, e.question_ref, e.error_reason, e.question_statement, e.bizu_notes, e.mastered,
               s.name as subject_name
        FROM error_notebook e
        JOIN subjects s ON e.subject_id = s.id
        WHERE e.user_id = ? AND (e.bizu_notes LIKE ? OR e.question_statement LIKE ? OR e.question_ref LIKE ? OR e.banca LIKE ? OR e.error_reason LIKE ?)
        LIMIT 8
        """, (uid, like_pat, like_pat, like_pat, like_pat, like_pat))
        for r in cursor.fetchall():
            bizu = r["bizu_notes"] or ""
            results.append({
                "type": "error",
                "category": "Caderno de Erros",
                "icon": "fa-book-skull",
                "color": "#f43f5e",
                "title": f"[{r['banca']}] {r['error_reason']}" + (f" - Ref: {r['question_ref']}" if r['question_ref'] else ""),
                "subtitle": f"{r['subject_name']} • {'Dominado' if r['mastered'] else 'Vulnerabilidade Ativa'}",
                "detail": bizu[:120] + ("..." if len(bizu) > 120 else ""),
                "tab": "cadernoerros",
                "ref_id": r["id"]
            })

        # 3. Notícias Policiais (Central de Inteligência)
        cursor.execute("""
        SELECT id, title, source, summary, pub_date, category, priority
        FROM news_feed
        WHERE title LIKE ? OR summary LIKE ? OR category LIKE ?
        ORDER BY CASE priority WHEN 'alta' THEN 1 WHEN 'media' THEN 2 ELSE 3 END ASC, id DESC
        LIMIT 8
        """, (like_pat, like_pat, like_pat))
        for r in cursor.fetchall():
            results.append({
                "type": "news",
                "category": "Notícias Policiais",
                "icon": "fa-newspaper",
                "color": "#ef4444" if r["priority"] == "alta" else ("#f59e0b" if r["priority"] == "media" else "#64748b"),
                "title": r["title"],
                "subtitle": f"{r['category']} • {r['source']} • {r['pub_date']}",
                "detail": (r["summary"] or "")[:120],
                "tab": "news",
                "ref_id": r["id"]
            })

        # 5. Simulations
        cursor.execute("""
        SELECT id, title, target_contest, date, total_questions, correct_answers, score
        FROM simulations
        WHERE user_id = ? AND (title LIKE ? OR target_contest LIKE ? OR notes LIKE ?)
        LIMIT 5
        """, (uid, like_pat, like_pat, like_pat))
        for r in cursor.fetchall():
            results.append({
                "type": "simulation",
                "category": "Simulados",
                "icon": "fa-bullseye",
                "color": "#f97316",
                "title": r["title"],
                "subtitle": f"{r['target_contest'] or 'Geral'} • {r['correct_answers']}/{r['total_questions']} itens ({r['score']} pts)",
                "detail": f"Data: {r['date']}",
                "tab": "simulations",
                "ref_id": r["id"]
            })

        # 6. Platforms
        cursor.execute("""
        SELECT id, title, url, category
        FROM study_platforms
        WHERE user_id = ? AND (title LIKE ? OR notes LIKE ? OR category LIKE ?)
        LIMIT 5
        """, (uid, like_pat, like_pat, like_pat))
        for r in cursor.fetchall():
            results.append({
                "type": "platform",
                "category": "Arsenal de Estudos",
                "icon": "fa-globe",
                "color": "#10b981",
                "title": r["title"],
                "subtitle": f"Categoria: {r['category']}",
                "detail": r["url"],
                "tab": "arsenal",
                "ref_id": r["id"]
            })

    return {"query": term, "total": len(results), "results": results}


# ==================== EXPORT CSV / EXCEL ====================
@app.get("/api/export/sessions.csv")
def export_sessions_csv(request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT ss.id, ss.date, ss.start_time, s.name as subject_name, COALESCE(t.name, 'Estudo Geral') as topic_name,
               ss.duration_seconds, ss.questions_correct, ss.questions_incorrect, ss.notes
        FROM study_sessions ss
        JOIN subjects s ON ss.subject_id = s.id
        LEFT JOIN topics t ON ss.topic_id = t.id
        WHERE ss.user_id = ?
        ORDER BY ss.date DESC, ss.id DESC
        """, (user["id"],))
        rows = cursor.fetchall()

    output = io.StringIO()
    output.write("\ufeff")  # UTF-8 BOM for Microsoft Excel
    writer = csv.writer(output, delimiter=';')
    writer.writerow([
        "ID", "Data", "Hora Inicio", "Disciplina", "Topico",
        "Duracao (Min)", "Duracao (Horas)", "Questoes Acertos",
        "Questoes Erros", "Total Questoes", "% Precisao", "Observacoes"
    ])

    for r in rows:
        mins = round(r["duration_seconds"] / 60)
        hrs = round(r["duration_seconds"] / 3600, 2)
        tot_q = r["questions_correct"] + r["questions_incorrect"]
        acc = round((r["questions_correct"] / tot_q * 100), 1) if tot_q > 0 else 0.0
        obs = (r["notes"] or "").replace("\n", " ").replace("\r", "")
        writer.writerow([
            r["id"], r["date"], r["start_time"] or "", r["subject_name"], r["topic_name"],
            mins, hrs, r["questions_correct"], r["questions_incorrect"], tot_q, f"{acc}%", obs
        ])

    filename = f"qap_turnos_estudo_{datetime.date.today().strftime('%Y%m%d')}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/export/errors.csv")
def export_errors_csv(request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT e.id, s.name as subject_name, COALESCE(t.name, 'Geral') as topic_name,
               e.banca, e.question_ref, e.error_reason, e.question_statement, e.bizu_notes,
               e.mastered, e.created_at
        FROM error_notebook e
        JOIN subjects s ON e.subject_id = s.id
        LEFT JOIN topics t ON e.topic_id = t.id
        WHERE e.user_id = ?
        ORDER BY e.mastered ASC, e.id DESC
        """, (user["id"],))
        rows = cursor.fetchall()

    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.writer(output, delimiter=';')
    writer.writerow([
        "ID", "Disciplina", "Topico", "Banca", "Referencia",
        "Tipo de Falha", "Enunciado da Questao", "Bizu Corretivo", "Status", "Data de Registro"
    ])

    for r in rows:
        status_txt = "Dominado (Superado)" if r["mastered"] else "Vulnerabilidade Ativa"
        stmt = (r["question_statement"] or "").replace("\n", " ").replace("\r", "")
        bizu = (r["bizu_notes"] or "").replace("\n", " ").replace("\r", "")
        writer.writerow([
            r["id"], r["subject_name"], r["topic_name"], r["banca"], r["question_ref"],
            r["error_reason"], stmt, bizu, status_txt, r["created_at"]
        ])

    filename = f"qap_caderno_erros_{datetime.date.today().strftime('%Y%m%d')}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/export/simulations.csv")
def export_simulations_csv(request: Request):
    user = require_user(request)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM simulations WHERE user_id = ? ORDER BY date DESC, id DESC", (user["id"],))
        rows = cursor.fetchall()

    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.writer(output, delimiter=';')
    writer.writerow([
        "ID", "Titulo do Simulado", "Concurso Alvo", "Data",
        "Total de Questoes", "Acertos", "Erros", "% Aproveitamento", "Nota Liquida", "Anotacoes"
    ])

    for r in rows:
        pct = round((r["correct_answers"] / r["total_questions"] * 100), 1) if r["total_questions"] > 0 else 0.0
        obs = (r["notes"] or "").replace("\n", " ").replace("\r", "")
        writer.writerow([
            r["id"], r["title"], r["target_contest"] or "", r["date"],
            r["total_questions"], r["correct_answers"], r["wrong_answers"], f"{pct}%", r["score"], obs
        ])

    filename = f"qap_simulados_{datetime.date.today().strftime('%Y%m%d')}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
