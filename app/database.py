import sqlite3
import os
from contextlib import contextmanager
from typing import Generator

BASE_ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.environ.get("DATA_DIR", "").strip()
if DATA_DIR:
    os.makedirs(DATA_DIR, exist_ok=True)
    DB_PATH = os.path.join(DATA_DIR, "concursos.db")
else:
    DB_PATH = os.path.join(BASE_ROOT, "concursos.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 15000")
    return conn

def enable_wal():
    """Ativa o modo WAL (mais resistente a quedas de energia e gravações simultâneas)."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
    finally:
        conn.close()

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Contas de Usuário (Multi-Usuário / Multi-Carreira)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT DEFAULT '',
            display_name TEXT NOT NULL DEFAULT 'Agente Operacional',
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # User profile / Tactical Rank
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            name TEXT NOT NULL DEFAULT 'Agente Operacional',
            target_role TEXT NOT NULL DEFAULT 'Polícia Civil - TO (Agente)',
            daily_goal_minutes INTEGER NOT NULL DEFAULT 240,
            weekly_goal_hours INTEGER NOT NULL DEFAULT 25,
            badge_icon TEXT DEFAULT 'fa-shield-halved',
            sound_enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Subjects (Disciplinas)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'Jurídica',
            color TEXT NOT NULL DEFAULT '#3b82f6',
            icon TEXT NOT NULL DEFAULT 'fa-scale-balanced',
            target_hours REAL DEFAULT 50.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Topics within subjects
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            theory_completed INTEGER DEFAULT 0,
            summary_completed INTEGER DEFAULT 0,
            questions_completed INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
        )
        """)

        # Study sessions (Turnos de Estudo / Horas registradas)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            topic_id INTEGER,
            date TEXT NOT NULL,
            start_time TEXT,
            duration_seconds INTEGER NOT NULL,
            questions_correct INTEGER DEFAULT 0,
            questions_incorrect INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE,
            FOREIGN KEY (topic_id) REFERENCES topics (id) ON DELETE SET NULL
        )
        """)

        # Revisions (Protocolo de Revisão Espaçada: 24h, 7d, 15d, 30d)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS revisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            topic_id INTEGER,
            title TEXT NOT NULL,
            scheduled_date TEXT NOT NULL,
            interval_stage INTEGER DEFAULT 1, -- 1=24h, 2=7d, 3=15d, 4=30d, 5=concluído
            completed INTEGER DEFAULT 0,
            completed_at TEXT,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE,
            FOREIGN KEY (topic_id) REFERENCES topics (id) ON DELETE SET NULL
        )
        """)

        # Radar de Concursos foi removido na v2.1 (consolidado em Notícias Policiais)
        cursor.execute("DROP TABLE IF EXISTS police_contests")

        # News feed (Notícias Policiais)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_feed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            category TEXT DEFAULT 'Policial',
            link TEXT DEFAULT '',
            pub_date TEXT NOT NULL,
            summary TEXT DEFAULT '',
            is_pinned INTEGER DEFAULT 0,
            priority TEXT DEFAULT 'normal', -- alta, media, normal
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Auto-migration for priority columns if updating existing database
        try:
            cursor.execute("ALTER TABLE news_feed ADD COLUMN priority TEXT DEFAULT 'normal'")
        except Exception:
            pass

        # Simulations & Tactical Mock Tests
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS simulations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            total_questions INTEGER NOT NULL,
            correct_answers INTEGER NOT NULL,
            wrong_answers INTEGER NOT NULL,
            score REAL NOT NULL,
            target_contest TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Study Platforms & Video / Question Bank Arsenal
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_platforms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'Banco de Questões', -- Banco de Questões, Videoaulas & Cursos, Jurisprudência, Simulados
            icon TEXT DEFAULT 'fa-globe',
            color TEXT DEFAULT '#3b82f6',
            notes TEXT DEFAULT '',
            is_pinned INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 1. Past Approvals & Achievements (Quadro de Honra)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contest_name TEXT NOT NULL,
            role TEXT NOT NULL,
            year INTEGER NOT NULL,
            position TEXT DEFAULT '',
            score TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Aprovado', -- Aprovado, Classificado, Convocado, Apto no TAF, Excedente
            badge_icon TEXT DEFAULT 'fa-medal',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 2. TAF Operacional (Physical Fitness Training)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS taf_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            pull_ups INTEGER DEFAULT 0, -- Barra fixa repetições
            pull_up_time REAL DEFAULT 0.0, -- Isometria em segundos (feminino)
            run_12min_meters INTEGER DEFAULT 0, -- Corrida 12 min em metros
            sit_ups INTEGER DEFAULT 0, -- Abdominal remador 1 min
            push_ups INTEGER DEFAULT 0, -- Flexão de braço
            swim_50m_seconds REAL DEFAULT 0.0, -- Natação 50m (específica PF)
            is_male INTEGER DEFAULT 1, -- 1 masculino, 0 feminino
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 3. Exam Countdowns (Dia D)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS exam_countdowns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            target_date TEXT NOT NULL, -- YYYY-MM-DD
            target_time TEXT DEFAULT '08:00',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 4. Law Reading Tracker (Radar de Lei Seca)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS law_reading_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            code_name TEXT NOT NULL, -- CF/88, Código Penal, CPP, Legislação Especial
            articles_read INTEGER NOT NULL,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 5. Caderno de Erros Operacional (Dossiê de Vulnerabilidades)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS error_notebook (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            topic_id INTEGER,
            banca TEXT DEFAULT 'Cebraspe', -- Cebraspe, FGV, Vunesp, FCC, AOCP
            question_ref TEXT DEFAULT '', -- ex: Q1982844 ou PF 2021
            error_reason TEXT NOT NULL, -- Pegadinha de Banca, Falta de Lei Seca, Falta de Atenção, Jurisprudência, Teoria
            question_statement TEXT DEFAULT '', -- Enunciado / questão
            bizu_notes TEXT NOT NULL, -- O Bizu da questão / comentário corretivo
            mastered INTEGER DEFAULT 0, -- 0 = Vulnerabilidade ativa, 1 = Dominada
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE,
            FOREIGN KEY (topic_id) REFERENCES topics (id) ON DELETE SET NULL
        )
        """)

        # 6. Oficina de Discursivas & Redações Policiais
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS discursive_essays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            agency TEXT DEFAULT 'Polícia Federal', -- PF, PRF, PC, PM
            lines_count INTEGER DEFAULT 30,
            score REAL DEFAULT 0.0,
            max_score REAL DEFAULT 10.0,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 7. Banco de Temas Quentes para Redação
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS essay_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            agency TEXT NOT NULL,
            axis TEXT NOT NULL, -- Segurança Pública, Tecnologia, Crime Organizado, Trânsito, Direitos Humanos
            description TEXT NOT NULL
        )
        """)
        
        # 8. Metadados do Sistema (Controle de inicialização única / persistência)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # v2.1 & v3.0 Multi-Tenant migrations
        for ddl in (
            "ALTER TABLE subjects ADD COLUMN weight REAL DEFAULT 1.0",
            "ALTER TABLE simulations ADD COLUMN subject_breakdown TEXT DEFAULT '[]'",
            "ALTER TABLE simulations ADD COLUMN cutoff_score REAL DEFAULT 0.0",
            "ALTER TABLE user_profile ADD COLUMN user_id INTEGER DEFAULT 1",
            "ALTER TABLE subjects ADD COLUMN user_id INTEGER DEFAULT 1",
            "ALTER TABLE study_sessions ADD COLUMN user_id INTEGER DEFAULT 1",
            "ALTER TABLE revisions ADD COLUMN user_id INTEGER DEFAULT 1",
            "ALTER TABLE simulations ADD COLUMN user_id INTEGER DEFAULT 1",
            "ALTER TABLE study_platforms ADD COLUMN user_id INTEGER DEFAULT 1",
            "ALTER TABLE approvals ADD COLUMN user_id INTEGER DEFAULT 1",
            "ALTER TABLE taf_records ADD COLUMN user_id INTEGER DEFAULT 1",
            "ALTER TABLE exam_countdowns ADD COLUMN user_id INTEGER DEFAULT 1",
            "ALTER TABLE law_reading_logs ADD COLUMN user_id INTEGER DEFAULT 1",
            "ALTER TABLE error_notebook ADD COLUMN user_id INTEGER DEFAULT 1",
            "ALTER TABLE discursive_essays ADD COLUMN user_id INTEGER DEFAULT 1",
        ):
            try:
                cursor.execute(ddl)
            except Exception:
                pass

        # Índices de desempenho & isolamento por usuário
        for idx in (
            "CREATE INDEX IF NOT EXISTS idx_sessions_date ON study_sessions(date)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_subject ON study_sessions(subject_id)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_topic ON study_sessions(topic_id)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_user ON study_sessions(user_id, date)",
            "CREATE INDEX IF NOT EXISTS idx_subjects_user ON subjects(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_topics_subject ON topics(subject_id)",
            "CREATE INDEX IF NOT EXISTS idx_revisions_sched ON revisions(user_id, scheduled_date, completed)",
            "CREATE INDEX IF NOT EXISTS idx_errors_subject ON error_notebook(user_id, subject_id)",
            "CREATE INDEX IF NOT EXISTS idx_law_date ON law_reading_logs(user_id, date)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_profile_user ON user_profile(user_id)",
        ):
            cursor.execute(idx)

        # Migração automática: se ainda não existe usuário na tabela users e já existem dados locais (ex: perfil id=1),
        # cria a conta principal (id=1, username='mikael') vinculando todo o histórico existente a ela.
        cursor.execute("SELECT COUNT(*) as cnt FROM users")
        if cursor.fetchone()["cnt"] == 0:
            cursor.execute("SELECT name FROM user_profile ORDER BY id ASC LIMIT 1")
            prof_row = cursor.fetchone()
            if prof_row:
                import hashlib, secrets
                salt = secrets.token_hex(16)
                dk = hashlib.pbkdf2_hmac("sha256", b"admin123", salt.encode("utf-8"), 200_000)
                pwd_hash = f"pbkdf2_sha256$200000${salt}${dk.hex()}"
                cursor.execute("""
                INSERT INTO users (id, username, email, display_name, password_hash, is_admin)
                VALUES (1, 'mikael', '', ?, ?, 1)
                """, (prof_row["name"] or "Agente Operacional", pwd_hash))
                for tbl in (
                    "user_profile", "subjects", "study_sessions", "revisions", "simulations",
                    "study_platforms", "approvals", "taf_records", "exam_countdowns",
                    "law_reading_logs", "error_notebook", "discursive_essays"
                ):
                    cursor.execute(f"UPDATE {tbl} SET user_id = 1 WHERE user_id IS NULL")

def is_system_seeded() -> bool:
    """Verifies whether the database has already completed its initial seed."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_metadata'")
        if not cursor.fetchone():
            return False
        cursor.execute("SELECT value FROM system_metadata WHERE key = 'initial_seed_completed'")
        row = cursor.fetchone()
        return bool(row and row["value"] == "true")

def mark_system_seeded():
    """Marks the initial seeding as permanently completed so user deletions and changes are never overwritten."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("""
        INSERT INTO system_metadata (key, value)
        VALUES ('initial_seed_completed', 'true')
        ON CONFLICT(key) DO UPDATE SET value = 'true', updated_at = CURRENT_TIMESTAMP
        """)
