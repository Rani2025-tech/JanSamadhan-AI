import sqlite3
import os
import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except ImportError:
    pwd_context = None



DB_PATH = "jansamadhan.db"
DATABASE_URL = os.getenv("DATABASE_URL")  # Set on Render for PostgreSQL

# Render injects postgres:// but psycopg2 needs postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def get_conn():
    if DATABASE_URL:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        return conn
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def _row_to_dict(row, cursor=None):
    """Convert a db row to dict regardless of backend."""
    if DATABASE_URL:
        if isinstance(row, dict):
            return row
        cols = [d[0] for d in cursor.description]
        return dict(zip(cols, row))
    return dict(row)

def _ph():
    """Return correct placeholder — %s for PostgreSQL, ? for SQLite."""
    return "%s" if DATABASE_URL else "?"

def _exec(c, sql, params=()):
    """Execute with correct placeholder style."""
    if DATABASE_URL:
        sql = sql.replace("?", "%s")
    c.execute(sql, params)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    tables = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'NO_ACCESS',
            department TEXT,
            active INTEGER DEFAULT 1,
            is_demo INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""",
        """
        CREATE TABLE IF NOT EXISTS rate_events (
            id TEXT PRIMARY KEY,
            key TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""",
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""",
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            user_name TEXT,
            session_id TEXT,
            issue TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""",
        """
        CREATE TABLE IF NOT EXISTS document_uploads (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            uploaded_by TEXT,
            chunks_created INTEGER DEFAULT 0,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""",
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id TEXT PRIMARY KEY,
            message_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            user_id TEXT,
            rating INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""",
        """
        CREATE TABLE IF NOT EXISTS query_logs (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            session_id TEXT,
            question TEXT NOT NULL,
            language TEXT DEFAULT 'en',
            response_time_ms INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""",
    ]
    for ddl in tables:
        c.execute(ddl)
    conn.commit()

    _migrate_users_and_roles(c, is_postgres=bool(DATABASE_URL))
    conn.commit()

    try:
        from backend.db.grievances import init_grievance_tables
        init_grievance_tables(conn)
    except Exception as e:
        print(f"Error initializing grievance tables: {e}")

    conn.close()

    try:
        ensure_admin()
    except Exception as e:
        print(f"Admin bootstrap check: {e}")

    try:
        ensure_demo_accounts()
    except Exception as e:
        print(f"Demo accounts bootstrap check: {e}")

def _migrate_users_and_roles(c, is_postgres: bool = False):
    """Idempotently migrate users table columns and map legacy roles."""
    if is_postgres:
        c.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'")
        cols = {row[0].lower() for row in c.fetchall()}
    else:
        c.execute("PRAGMA table_info(users)")
        cols = {row[1].lower() for row in c.fetchall()}

    if "department" not in cols:
        c.execute("ALTER TABLE users ADD COLUMN department TEXT")
    if "active" not in cols:
        c.execute("ALTER TABLE users ADD COLUMN active INTEGER DEFAULT 1")
    if "is_demo" not in cols:
        c.execute("ALTER TABLE users ADD COLUMN is_demo INTEGER DEFAULT 0")

    # Map legacy role values:
    c.execute("UPDATE users SET role = 'ADMIN' WHERE role = 'admin'")
    c.execute("UPDATE users SET role = 'NO_ACCESS' WHERE role NOT IN ('ADMIN', 'DEPARTMENT_OFFICIAL')")

    # Migrate grievances table (add pin_hash if not present)
    try:
        if is_postgres:
            c.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'grievances'")
            gcols = {row[0].lower() for row in c.fetchall()}
        else:
            c.execute("PRAGMA table_info(grievances)")
            gcols = {row[1].lower() for row in c.fetchall()}
        if gcols and "pin_hash" not in gcols:
            c.execute("ALTER TABLE grievances ADD COLUMN pin_hash TEXT")
    except Exception:
        pass

# Precompute dummy hash for timing attack mitigation during password verification
DUMMY_BCRYPT_HASH = pwd_context.hash("dummy_auth_placeholder_timing_attack_mitigation") if pwd_context else "0" * 64

def hash_password(password: str) -> str:
    if pwd_context:
        return pwd_context.hash(password)
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    # Support legacy sha256 hashes during migration
    import hashlib
    if len(hashed) == 64 and pwd_context:
        if hashlib.sha256(plain.encode()).hexdigest() == hashed:
            return True
    if pwd_context:
        try:
            return pwd_context.verify(plain, hashed)
        except Exception:
            return False
    import hashlib
    return hashlib.sha256(plain.encode()).hexdigest() == hashed

def record_event(key: str):
    """Record a rate-limit event with opportunistic cleanup of events > 1 day old."""
    conn = get_conn()
    c = conn.cursor()
    event_id = str(uuid.uuid4())
    try:
        if DATABASE_URL:
            c.execute("DELETE FROM rate_events WHERE created_at < NOW() - INTERVAL '1 day'")
            c.execute("INSERT INTO rate_events (id, key, created_at) VALUES (%s, %s, NOW())", (event_id, key))
        else:
            c.execute("DELETE FROM rate_events WHERE created_at < datetime('now', '-1 day')")
            c.execute("INSERT INTO rate_events (id, key, created_at) VALUES (?, ?, datetime('now'))", (event_id, key))
        conn.commit()
    finally:
        conn.close()

def clear_events(key: str):
    """Clear recorded rate events for a given key upon successful action."""
    conn = get_conn()
    c = conn.cursor()
    try:
        _exec(c, "DELETE FROM rate_events WHERE key = ?", (key,))
        conn.commit()
    finally:
        conn.close()

def too_many(key: str, limit: int, window_seconds: int) -> bool:
    """Return True if event count in the last window_seconds exceeds or equals limit."""
    conn = get_conn()
    c = conn.cursor()
    try:
        if DATABASE_URL:
            c.execute(
                "SELECT COUNT(*) FROM rate_events WHERE key = %s AND created_at >= NOW() - (%s || ' seconds')::INTERVAL",
                (key, str(window_seconds))
            )
        else:
            c.execute(
                "SELECT COUNT(*) FROM rate_events WHERE key = ? AND created_at >= datetime('now', ?)",
                (key, f"-{window_seconds} seconds")
            )
        count = c.fetchone()[0] or 0
        return count >= limit
    finally:
        conn.close()

def ensure_admin():
    """Ensure system administrator user exists without overwriting existing password."""
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        raise ValueError("ADMIN_PASSWORD environment variable is not set")
    if len(admin_password) < 8:
        raise ValueError("ADMIN_PASSWORD must be at least 8 characters long")

    admin_email = os.getenv("ADMIN_EMAIL", "admin@jansamadhan.local").strip().lower()
    conn = get_conn()
    c = conn.cursor()
    try:
        _exec(c, "SELECT id, email, password, role, active FROM users WHERE LOWER(email) = ?", (admin_email,))
        row = c.fetchone()
        if row:
            user = _row_to_dict(row, c)
            if user.get("role") != "ADMIN" or user.get("active") != 1:
                _exec(c, "UPDATE users SET role = 'ADMIN', active = 1 WHERE LOWER(email) = ?", (admin_email,))
                conn.commit()
        else:
            admin_id = str(uuid.uuid4())
            hashed = hash_password(admin_password)
            _exec(c,
                "INSERT INTO users (id, name, email, password, role, department, active) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (admin_id, "System Administrator", admin_email, hashed, "ADMIN", None, 1)
            )
            conn.commit()
    finally:
        conn.close()

def get_demo_official_department() -> str:
    env_dept = os.getenv("DEMO_OFFICIAL_DEPARTMENT")
    if env_dept:
        return env_dept.strip().strip('"').strip("'")
    dept_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "departments.json")
    if os.path.exists(dept_file):
        try:
            with open(dept_file, "r", encoding="utf-8") as f:
                depts = json.load(f)
                for d in depts:
                    if d.get("category") == "Water Supply" and d.get("department"):
                        return d["department"]
                if depts and depts[0].get("department"):
                    return depts[0]["department"]
        except Exception:
            pass
    return "Public Health Engineering / Water Board"

def ensure_demo_accounts():
    """Create demo accounts for judges if DEMO_MODE=1. Idempotent."""
    demo_mode = os.getenv("DEMO_MODE", "0").strip()
    if demo_mode != "1":
        return

    demo_dept = get_demo_official_department()
    conn = get_conn()
    c = conn.cursor()
    try:
        # 1. Demo Admin
        admin_email = "demo.admin@jansamadhan.demo"
        _exec(c, "SELECT id, name, role, is_demo FROM users WHERE LOWER(email) = ?", (admin_email,))
        row = c.fetchone()
        if row:
            _exec(c, "UPDATE users SET name = 'Demo Administrator (demo)', role = 'ADMIN', department = NULL, active = 1, is_demo = 1 WHERE LOWER(email) = ?", (admin_email,))
        else:
            admin_id = str(uuid.uuid4())
            rand_pwd = secrets.token_urlsafe(32)
            hashed = hash_password(rand_pwd)
            _exec(c,
                "INSERT INTO users (id, name, email, password, role, department, active, is_demo) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (admin_id, "Demo Administrator (demo)", admin_email, hashed, "ADMIN", None, 1, 1)
            )

        # 2. Demo Official
        official_email = "demo.official@jansamadhan.demo"
        _exec(c, "SELECT id, name, role, department, is_demo FROM users WHERE LOWER(email) = ?", (official_email,))
        row = c.fetchone()
        if row:
            _exec(c, "UPDATE users SET name = 'Demo Official (demo)', role = 'DEPARTMENT_OFFICIAL', department = ?, active = 1, is_demo = 1 WHERE LOWER(email) = ?", (demo_dept, official_email))
        else:
            off_id = str(uuid.uuid4())
            rand_pwd = secrets.token_urlsafe(32)
            hashed = hash_password(rand_pwd)
            _exec(c,
                "INSERT INTO users (id, name, email, password, role, department, active, is_demo) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (off_id, "Demo Official (demo)", official_email, hashed, "DEPARTMENT_OFFICIAL", demo_dept, 1, 1)
            )
        conn.commit()
    finally:
        conn.close()

def get_user_by_id(user_id: str) -> Optional[dict]:
    conn = get_conn()
    c = conn.cursor()
    try:
        _exec(c, "SELECT id, name, email, role, department, active, is_demo, created_at FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        return _row_to_dict(row, c) if row else None
    finally:
        conn.close()

def get_user_by_email(email: str) -> Optional[dict]:
    conn = get_conn()
    c = conn.cursor()
    try:
        _exec(c, "SELECT id, name, email, role, department, active, is_demo, created_at FROM users WHERE LOWER(email) = ?", (email.strip().lower(),))
        row = c.fetchone()
        return _row_to_dict(row, c) if row else None
    finally:
        conn.close()

def create_staff_user(name: str, email: str, password: str, department: str) -> dict:
    conn = get_conn()
    c = conn.cursor()
    user_id = str(uuid.uuid4())
    hashed = hash_password(password)
    email_clean = email.strip().lower()
    try:
        _exec(c,
            "INSERT INTO users (id, name, email, password, role, department, active) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, name.strip(), email_clean, hashed, "DEPARTMENT_OFFICIAL", department, 1)
        )
        conn.commit()
        return {
            "id": user_id,
            "name": name.strip(),
            "email": email_clean,
            "role": "DEPARTMENT_OFFICIAL",
            "department": department,
            "active": 1
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def list_staff_users() -> list:
    conn = get_conn()
    c = conn.cursor()
    try:
        _exec(c, "SELECT id, name, email, role, department, active, created_at FROM users WHERE role = 'DEPARTMENT_OFFICIAL' ORDER BY created_at DESC")
        return [_row_to_dict(r, c) for r in c.fetchall()]
    finally:
        conn.close()

def update_staff_user(user_id: str, active: Optional[int] = None, department: Optional[str] = None, password: Optional[str] = None) -> Optional[dict]:
    conn = get_conn()
    c = conn.cursor()
    try:
        updates = []
        params = []
        if active is not None:
            updates.append("active = ?")
            params.append(int(active))
        if department is not None:
            updates.append("department = ?")
            params.append(department)
        if password is not None:
            updates.append("password = ?")
            params.append(hash_password(password))

        if not updates:
            return get_user_by_id(user_id)

        params.append(user_id)
        sql = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        _exec(c, sql, tuple(params))
        conn.commit()
        return get_user_by_id(user_id)
    finally:
        conn.close()

def create_user(name: str, email: str, password: str) -> dict:
    conn = get_conn()
    c = conn.cursor()
    user_id = str(uuid.uuid4())
    hashed = hash_password(password)
    try:
        _exec(c,
            "INSERT INTO users (id, name, email, password, role) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, email, hashed, "NO_ACCESS")
        )
        conn.commit()
        return {"id": user_id, "name": name, "email": email, "role": "NO_ACCESS"}
    except Exception:
        conn.rollback()
        return None
    finally:
        conn.close()

def login_user(email: str, password: str) -> Optional[dict]:
    conn = get_conn()
    c = conn.cursor()
    try:
        _exec(c, "SELECT * FROM users WHERE LOWER(email)=?", (email.strip().lower(),))
        row = c.fetchone()
        if not row:
            verify_password(password, DUMMY_BCRYPT_HASH)
            return None
        user = _row_to_dict(row, c)
        if user.get("is_demo") == 1:
            verify_password(password, DUMMY_BCRYPT_HASH)
            return None
        if user.get("active") != 1:
            verify_password(password, DUMMY_BCRYPT_HASH)
            return None
        if user.get("role") not in ("ADMIN", "DEPARTMENT_OFFICIAL"):
            verify_password(password, DUMMY_BCRYPT_HASH)
            return None
        if not verify_password(password, user["password"]):
            return None
        res = dict(user)
        res.pop("password", None)
        return res
    finally:
        conn.close()

def create_session(user_id: str, title: str = "New Chat") -> str:
    conn = get_conn()
    c = conn.cursor()
    session_id = str(uuid.uuid4())
    _exec(c,
        "INSERT INTO chat_sessions (id, user_id, title) VALUES (?, ?, ?)",
        (session_id, user_id, title)
    )
    conn.commit()
    conn.close()
    return session_id

def update_session_title(session_id: str, title: str):
    conn = get_conn()
    c = conn.cursor()
    _exec(c, "UPDATE chat_sessions SET title=? WHERE id=?", (title[:50], session_id))
    conn.commit()
    conn.close()

def save_message(session_id: str, role: str, content: str):
    conn = get_conn()
    c = conn.cursor()
    msg_id = str(uuid.uuid4())
    _exec(c,
        "INSERT INTO chat_messages (id, session_id, role, content) VALUES (?, ?, ?, ?)",
        (msg_id, session_id, role, content)
    )
    conn.commit()
    conn.close()

def get_sessions(user_id: str) -> list:
    conn = get_conn()
    c = conn.cursor()
    _exec(c,
        "SELECT * FROM chat_sessions WHERE user_id=? ORDER BY created_at DESC LIMIT 20",
        (user_id,)
    )
    rows = [_row_to_dict(r, c) for r in c.fetchall()]
    conn.close()
    return rows

def get_messages(session_id: str) -> list:
    conn = get_conn()
    c = conn.cursor()
    _exec(c,
        "SELECT * FROM chat_messages WHERE session_id=? ORDER BY created_at ASC",
        (session_id,)
    )
    rows = [_row_to_dict(r, c) for r in c.fetchall()]
    conn.close()
    return rows

def create_ticket(user_id: str, user_name: str, session_id: str, issue: str) -> str:
    conn = get_conn()
    c = conn.cursor()
    ticket_id = "TKT-" + str(uuid.uuid4())[:8].upper()
    _exec(c,
        "INSERT INTO tickets (id, user_id, user_name, session_id, issue) VALUES (?, ?, ?, ?, ?)",
        (ticket_id, user_id, user_name, session_id, issue)
    )
    conn.commit()
    conn.close()
    return ticket_id

def get_all_tickets() -> list:
    conn = get_conn()
    c = conn.cursor()
    _exec(c, "SELECT * FROM tickets ORDER BY created_at DESC")
    rows = [_row_to_dict(r, c) for r in c.fetchall()]
    conn.close()
    return rows

def update_ticket_status(ticket_id: str, status: str):
    conn = get_conn()
    c = conn.cursor()
    _exec(c, "UPDATE tickets SET status=? WHERE id=?", (status, ticket_id))
    conn.commit()
    conn.close()

def get_stats() -> dict:
    conn = get_conn()
    c = conn.cursor()

    def _scalar(sql):
        _exec(c, sql)
        return c.fetchone()[0] or 0

    total_users       = _scalar("SELECT COUNT(*) FROM users WHERE role='user'")
    total_tickets     = _scalar("SELECT COUNT(*) FROM tickets")
    open_tickets      = _scalar("SELECT COUNT(*) FROM tickets WHERE status='open'")
    resolved_tickets  = _scalar("SELECT COUNT(*) FROM tickets WHERE status='resolved'")
    total_messages    = _scalar("SELECT COUNT(*) FROM chat_messages")
    total_documents   = _scalar("SELECT COUNT(*) FROM document_uploads")
    positive_feedback = _scalar("SELECT COUNT(*) FROM feedback WHERE rating=1")
    total_feedback    = _scalar("SELECT COUNT(*) FROM feedback")

    _exec(c, "SELECT COUNT(*) FROM chat_messages WHERE role='user' AND DATE(created_at)=CURRENT_DATE")
    queries_today = c.fetchone()[0] or 0

    _exec(c, "SELECT AVG(response_time_ms) FROM query_logs WHERE response_time_ms IS NOT NULL")
    avg_response_ms = c.fetchone()[0]

    _exec(c, "SELECT language, COUNT(*) as cnt FROM query_logs GROUP BY language ORDER BY cnt DESC")
    language_breakdown = {row[0]: row[1] for row in c.fetchall()}

    conn.close()
    return {
        "total_users": total_users,
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "resolved_tickets": resolved_tickets,
        "total_messages": total_messages,
        "queries_today": queries_today,
        "total_documents": total_documents,
        "avg_response_ms": round(avg_response_ms) if avg_response_ms else 0,
        "language_breakdown": language_breakdown,
        "positive_feedback": positive_feedback,
        "total_feedback": total_feedback
    }

def log_document_upload(filename: str, uploaded_by: str, chunks_created: int):
    conn = get_conn()
    c = conn.cursor()
    _exec(c,
        "INSERT INTO document_uploads (id, filename, uploaded_by, chunks_created) VALUES (?, ?, ?, ?)",
        (str(uuid.uuid4()), filename, uploaded_by, chunks_created)
    )
    conn.commit()
    conn.close()

def get_document_uploads() -> list:
    conn = get_conn()
    c = conn.cursor()
    _exec(c, "SELECT * FROM document_uploads ORDER BY uploaded_at DESC")
    rows = [_row_to_dict(r, c) for r in c.fetchall()]
    conn.close()
    return rows

def save_feedback(message_id: str, session_id: str, user_id: str, rating: int):
    conn = get_conn()
    c = conn.cursor()
    _exec(c,
        "INSERT INTO feedback (id, message_id, session_id, user_id, rating) VALUES (?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), message_id, session_id, user_id, rating)
    )
    conn.commit()
    conn.close()

def log_query(user_id: str, session_id: str, question: str, language: str, response_time_ms: int):
    conn = get_conn()
    c = conn.cursor()
    _exec(c,
        "INSERT INTO query_logs (id, user_id, session_id, question, language, response_time_ms) VALUES (?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), user_id, session_id, question, language, response_time_ms)
    )
    conn.commit()
    conn.close()
